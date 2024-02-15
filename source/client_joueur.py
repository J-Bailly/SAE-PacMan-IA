# coding: utf-8
"""
            SAE1.02 PACMAN IUT'O
         BUT1 Informatique 2023-2024

        Module client_joueur.py
        Ce module contient le programme principal d'un joueur
        il s'occupe des communications avec le serveur
            - envois des ordres
            - recupération de l'état du jeu
        la fonction mon_IA est celle qui contient la stratégie de
        jeu du joueur.

"""
import argparse
import random

import case
import client
import const
import joueur
import plateau

prec='X'


def dico_distance(labyrinthe, pos_depart):
    """ Fonction qui à partir d'un labyrinthe et d'une position de départ, retourne un dictionnaire contenant les distances
    de chaque elements du plateau par rapport à la position de départ pour chaque direction possible

    Args:
        labyrinthe: le labyrinthe
        pos_depart: la position de départ

    Returns:
        dict: un dictionnaire ou les clés sont les directions possibles et les valeurs sont des dictionnaires contenant les distances de chaque éléments du plateau
    """

    res = {}
    for direction in plateau.directions_possibles(labyrinthe, pos_depart):
        dir_dist = plateau.analyse_plateau(labyrinthe, pos_depart, direction, 64)

        if dir_dist is not None:
            res[direction] = dir_dist

    return res


def get_fantome_plus_loin(couleur, distances, distance_contre_max=16):
    """ Fonction qui retourne la direction permettant de s'éloigner le plus des fantomes

    Args:
        couleur: la couleur du joueur
        distances: le dictionnaire retourné par la fonction dico_distance contenant les distances de chaque éléments du plateau
        distance_contre_max (int, optional): Distance maximal à laquelle il est intéressant de prendre un objet contre les fantomes. Defaults to 16.

    Returns:
        str: la direction permettant de s'éloigner le plus des fantomes
    """
    directions = []
    distance_max = float("-inf")
    
    # On parcourt les directions possibles afin de trouver quelles directions permettent de s'éloigner le plus des fantomes
    for direction in distances:
        # Si le fantome le plus proche est de la même couleur que le joueur, on le retire
        if distances[direction]["fantomes"][0][1].upper() == couleur.upper():
            distances[direction]["fantomes"].pop(0)

        # On regarde si le fantome est plus loin que le fantome le plus loin actuel
        if distances[direction]["fantomes"][0][0] > distance_max:
            directions = [direction]
            distance_max = distances[direction]["fantomes"][0][0]
        
        # Si la distance du fantome le plus loin est égale à la distance max, on ajoute la direction à la liste
        elif distances[direction]["fantomes"][0][0] == distance_max:
            directions.append(direction)

    # Si il n'y a qu'une direction possible, on la retourne
    if len(directions) == 1:
        return directions[0]
    
    # Sinon, on regarde les objets dans ces directions afin de choisir la direction la plus intéressante
    min_distance_contre = float("inf")
    min_direction_contre = None

    min_distance_score = float("inf")
    min_direction_score = None

    for direction in directions:
        for objet in distances[direction]["objets"]:
            # Si l'objet est un objet contre les fantomes
            if objet[0] <= distance_contre_max and (objet[1] == const.GLOUTON or objet[1] == const.IMMOBILITE  or objet[1] == const.TELEPORTATION):
                if objet[0] < min_distance_contre:
                    min_distance_contre = objet[0]
                    min_direction_contre = direction

            # Si l'objet est un objet de score
            elif objet[0] < min_distance_score:
                min_distance_score = objet[0]
                min_direction_score = direction

    # Si il y a un objet contre les fantomes à proximité, on le prend sinon on prend l'objet de score le plus proche
    return min_direction_contre if min_direction_contre is not None else min_direction_score


def get_fantome_plus_proche(couleur, distances):
    """ Fonction qui retourne la direction permettant de se rapprocher le plus des fantomes

    Args:
        couleur (str): la couleur du joueur
        distances (dict): le dictionnaire retourné par la fonction dico_distance contenant les distances de chaque éléments du plateau

    Returns:
        str: la direction permettant de se rapprocher le plus des fantomes
    """
    
    for direction in distances:
        # Si le fantome le plus proche est de la même couleur que le joueur, on le retire afin de l'ignorer
        if distances[direction]["fantomes"][0][1].upper() == couleur.upper():
            distances[direction]["fantomes"].pop(0)

    # On retourne la direction permettant de se rapprocher le plus des fantomes
    return min(distances, key=lambda direction: distances[direction]["fantomes"][0][0])


def get_pacman_plus_loin(couleur, distances):
    """ Fonction qui retourne la direction permettant de s'éloigner le plus des pacmans

    Args:
        couleur (str): la couleur du joueur
        distances (dict): le dictionnaire retourné par la fonction dico_distance contenant les distances de chaque éléments du plateau

    Returns:
        str: la direction permettant de s'éloigner le plus des pacmans
    """

    for direction in distances:
        # Si le fantome le plus proche est de la même couleur que le joueur, on le retire afin de l'ignorer
        if distances[direction]["pacmans"][0][1].upper() == couleur.upper():
            distances[direction]["pacmans"].pop(0)

    # On retourne la direction permettant de s'éloigner le plus des pacmans
    return max(distances, key=lambda direction: distances[direction]["pacmans"][0][0])


def deplacement_fantome(couleur, joueurs, labyrinthe):
    """ Fonction qui retourne la direction du fantome

    Args:
        couleur (str): la couleur du joueur
        joueurs (dict): le dictionnaire contenant les informations des joueurs
        labyrinthe (Plateau): le labyrinthe
        
    Returns:
        str: la direction du fantome
    """

    distances = dico_distance(labyrinthe, joueurs[couleur]["pos_fantome"])

    for direction in distances:
        # Si le fantome le plus proche est de la même couleur que le joueur, on le retire afin de l'ignorer
        if distances[direction]["pacmans"][0][1].upper() == couleur.upper():
            distances[direction]["pacmans"].pop(0)

        for pacman in distances[direction]["pacmans"]:
            # Si le pacman à un glouton, et qu'il dure assez longtemps pour qu'il puisse atteindre le fantome
            if joueurs[pacman[1]]["objets"][const.GLOUTON] - pacman[0] > 0:

                # Si le fantome est à moins de 3 cases du pacman
                if pacman[0] < 3:
                    # Si le joueur a ses 3 faux mouvements, il se téléporte
                    if joueurs[couleur]["nb_faux_mvt"] == 1:
                        return "!"
                    
                    else:
                        # Sinon on s'enfuit
                        return get_pacman_plus_loin(couleur, distances)
                
                # Si le fantome est à plus de 3 cases du pacman, on l'ignore
                distances[direction]["pacmans"].remove(pacman)

    # Si il n'y a plus de pacmans, on retourne une direction aléatoire
    if len(distances) == 0:
        return random.choice(plateau.directions_possibles(labyrinthe, joueurs[couleur]["pos_fantome"]))
    
    # On retourne la direction permettant de se rapprocher le plus des pacmans
    return min(distances, key=lambda direction: distances[direction]["pacmans"][0][0])
    

def deplacement_pacman(couleur, joueurs, labyrinthe):
    distances = dico_distance(labyrinthe, joueurs[couleur]["pos_pacman"])
    
    # On retire le fantome de la même couleur que le joueur
    for direction in distances:
        if distances[direction]["fantomes"][0][1].upper() == couleur.upper():
            distances[direction]["fantomes"].pop(0)

    # Si il y a un fantome dans les 3 cases et que le joueur n'a pas ses 3 faux mouvements, on les fait
    fantome_le_plus_proche = get_fantome_plus_proche(couleur, distances)
    fantome_le_plus_loin = get_fantome_plus_loin(couleur, distances)
    if distances[fantome_le_plus_proche]["fantomes"][0][0] > joueurs[couleur]["nb_faux_mvt"] and joueurs[couleur]["nb_faux_mvt"] != 1:
        return "!"
    
    # Si il y a un fantome dans les 3 cases et que le joueur a ses 3 faux mouvements, on se téléporte sinon on s'enfuit
    if distances[fantome_le_plus_proche]["fantomes"][0][0] < 3 and joueurs[couleur]["objets"][const.GLOUTON] - 1 <= 0:
        if joueurs[couleur]["nb_faux_mvt"] == 1:
            return "!"  
        
        return fantome_le_plus_loin
    
    # Si le joueur a ses 3 faux mouvements, et qu'il n'y a pas de fantome dans les 3 cases, on cherche les objets
    objets = []
    for direction in distances:
        for objet in distances[direction]["objets"]:
            objets.append((direction, objet[0], objet[1]))

    # Si il y a des objets, on prend l'objet le plus intéressant (rapport score / distance)
    if len(objets) > 0:
        return max(objets, key=lambda objet:  const.PROP_OBJET[objet[2]][0] / objet[1])[0]
    
    # Si le joueur ne trouve rien d'intéressant, il se téléporte
    return "!"
     

def mon_IA(ma_couleur: str,carac_jeu, plan, les_joueurs):
    """ Cette fonction permet de calculer les deux actions du joueur de couleur ma_couleur
        en fonction de l'état du jeu décrit par les paramètres. 
        Le premier caractère est parmi XSNOE X indique pas de peinture et les autres
        caractères indique la direction où peindre (Nord, Sud, Est ou Ouest)
        Le deuxième caractère est parmi SNOE indiquant la direction où se déplacer.

    Args:
        ma_couleur (str): un caractère en majuscule indiquant la couleur du jeur
        carac_jeu (str): une chaine de caractères contenant les caractéristiques
                                   de la partie séparées par des ;
             duree_act;duree_tot;reserve_init;duree_obj;penalite;bonus_touche;bonus_rechar;bonus_objet           
        plan (str): le plan du plateau comme comme indiqué dans le sujet
        les_joueurs (str): le liste des joueurs avec leur caractéristique (1 joueur par ligne)
        couleur; nom; nb_points; nb_faux_mvt; pos_pacman; pos_fantome; objets
        
    Returns:
        str: une chaine de deux caractères en majuscules indiquant la direction de peinture
            et la direction de déplacement
    """

    # decodage des informations provenant du serveur
    joueurs={}
    for ligne in les_joueurs.split('\n'):
        le_joueur = joueur.joueur_from_str(ligne)
        joueurs[joueur.get_couleur(le_joueur)] = le_joueur
     
    labyrinthe = plateau.Plateau(plan)
    return deplacement_pacman(ma_couleur, joueurs, labyrinthe) + deplacement_fantome(ma_couleur, joueurs, labyrinthe)


if __name__=="__main__":
    parser = argparse.ArgumentParser()  
    parser.add_argument("--equipe", dest="nom_equipe", help="nom de l'équipe", type=str, default='Non fournie')
    parser.add_argument("--serveur", dest="serveur", help="serveur de jeu", type=str, default='localhost')
    parser.add_argument("--port", dest="port", help="port de connexion", type=int, default=1111)
    
    args = parser.parse_args()
    le_client=client.ClientCyber()
    le_client.creer_socket(args.serveur,args.port)
    le_client.enregistrement(args.nom_equipe,"joueur")
    ok=True
    while ok:
        ok,id_joueur,le_jeu=le_client.prochaine_commande()
        if ok:
            carac_jeu,le_plateau,les_joueurs=le_jeu.split("--------------------\n")
            actions_joueur=mon_IA(id_joueur,carac_jeu,le_plateau,les_joueurs[:-1])
            le_client.envoyer_commande_client(actions_joueur)
            # le_client.afficher_msg("sa reponse  envoyée "+str(id_joueur)+args.nom_equipe)
    le_client.afficher_msg("terminé")

from flask import Flask, request, jsonify, render_template
from datetime import datetime
import json
import os
import re

app = Flask(__name__)

# Configuration
FICHIER_DONNEES = 'donnees.json'
app.config['JSON_SORT_KEYS'] = False

# ====== UTILITAIRES ======

def charger_donnees():
    """Charge les données depuis le fichier JSON"""
    if os.path.exists(FICHIER_DONNEES):
        try:
            with open(FICHIER_DONNEES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erreur lors de la lecture : {e}")
            return {"registre": [], "commentaires": []}
    return {"registre": [], "commentaires": []}

def sauvegarder_donnees(donnees):
    """Sauvegarde les données dans le fichier JSON"""
    try:
        with open(FICHIER_DONNEES, 'w', encoding='utf-8') as f:
            json.dump(donnees, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Erreur lors de la sauvegarde : {e}")
        raise

def valider_email(email):
    """Validation du format email avec regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def valider_telephone(telephone):
    """Validation basique du numéro de téléphone"""
    # Enlever les espaces et tirets, vérifier qu'il y a au moins 10 chiffres
    clean_phone = telephone.replace(' ', '').replace('-', '').replace('.', '')
    return len(clean_phone) >= 10 and clean_phone.isdigit()

def valider_entree(donnees, champs_requis):
    """Valide les champs requis"""
    for champ in champs_requis:
        if champ not in donnees or not str(donnees[champ]).strip():
            return False, f"Champ manquant ou vide : {champ}"
    
    # Validation email
    email_key = 'mail' if 'mail' in donnees else 'email'
    if email_key in donnees and donnees[email_key]:
        if not valider_email(donnees[email_key]):
            return False, "Format email invalide"
    
    # Validation téléphone
    telephone_key = 'num' if 'num' in donnees else 'telephone'
    if telephone_key in donnees and donnees[telephone_key]:
        if not valider_telephone(donnees[telephone_key]):
            return False, "Numéro de téléphone invalide (minimum 10 chiffres)"
    
    return True, None

def nettoyer_donnees(donnees):
    """Nettoie les données en enlevant les espaces superflus"""
    return {k: str(v).strip() if isinstance(v, str) else v for k, v in donnees.items()}

# ====== ROUTES ======

@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/submit', methods=['POST'])
def soumettre():
    """Traite la soumission du formulaire HTML"""
    try:
        donnees = nettoyer_donnees(request.form.to_dict())
        requis = ['name', 'prename', 'num', 'mail']
        
        valide, erreur = valider_entree(donnees, requis)
        if not valide:
            return render_template('erreur.html', message=erreur), 400
        
        toutes_donnees = charger_donnees()
        nouvel_id = len(toutes_donnees['registre']) + 1
        
        # Ajouter à registre
        toutes_donnees['registre'].append({
            "id": nouvel_id,
            "nom": donnees['name'],
            "prenom": donnees['prename'],
            "telephone": donnees['num'],
            "email": donnees['mail'],
            "date_creation": datetime.now().isoformat()
        })
        
        # Ajouter commentaires
        toutes_donnees['commentaires'].append({
            "id": len(toutes_donnees['commentaires']) + 1,
            "user_id": nouvel_id,
            "impression": donnees.get('imp', ''),
            "avis": donnees.get('Avis', '')
        })
        
        sauvegarder_donnees(toutes_donnees)
        return render_template('succes.html', user_id=nouvel_id)
    
    except Exception as e:
        print(f"Erreur lors de la soumission : {e}")
        return render_template('erreur.html', message="Une erreur est survenue lors de l'enregistrement"), 500

@app.route('/api/donnees', methods=['GET'])
def obtenir_tous():
    """Retourne tous les enregistrements et commentaires"""
    try:
        return jsonify(charger_donnees())
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route('/api/donnees', methods=['POST'])
def creer():
    """Crée un nouvel enregistrement via API"""
    try:
        nouveau = request.get_json()
        if not nouveau:
            return jsonify({"erreur": "Corps de la requête vide"}), 400
        
        nouveau = nettoyer_donnees(nouveau)
        requis = ['nom', 'prenom', 'telephone', 'email']
        
        valide, erreur = valider_entree(nouveau, requis)
        if not valide:
            return jsonify({"erreur": erreur}), 400
        
        toutes_donnees = charger_donnees()
        nouvel_id = len(toutes_donnees['registre']) + 1
        
        nouveau['id'] = nouvel_id
        nouveau['date_creation'] = datetime.now().isoformat()
        toutes_donnees['registre'].append(nouveau)
        
        toutes_donnees['commentaires'].append({
            "id": len(toutes_donnees['commentaires']) + 1,
            "user_id": nouvel_id,
            "impression": nouveau.get("impression", ""),
            "avis": nouveau.get("avis", "")
        })
        
        sauvegarder_donnees(toutes_donnees)
        return jsonify({
            "message": "Données ajoutées avec succès",
            "id": nouvel_id,
            "utilisateur": nouveau
        }), 201
    
    except Exception as e:
        print(f"Erreur lors de la création : {e}")
        return jsonify({"erreur": str(e)}), 500

@app.route('/api/donnees/<int:user_id>', methods=['GET'])
def obtenir_un(user_id):
    """Retourne un utilisateur spécifique"""
    try:
        toutes_donnees = charger_donnees()
        utilisateur = next((u for u in toutes_donnees['registre'] if u['id'] == user_id), None)
        if not utilisateur:
            return jsonify({"erreur": "Utilisateur non trouvé"}), 404
        return jsonify(utilisateur)
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route('/api/donnees/<int:user_id>', methods=['PUT'])
def modifier(user_id):
    """Modifie un utilisateur existant"""
    try:
        toutes_donnees = charger_donnees()
        utilisateur = next((u for u in toutes_donnees['registre'] if u['id'] == user_id), None)
        if not utilisateur:
            return jsonify({"erreur": "Utilisateur non trouvé"}), 404
        
        mises_a_jour = request.get_json()
        if not mises_a_jour:
            return jsonify({"erreur": "Corps de la requête vide"}), 400
        
        mises_a_jour = nettoyer_donnees(mises_a_jour)
        
        # Valider l'email si présent
        if 'email' in mises_a_jour and mises_a_jour['email']:
            if not valider_email(mises_a_jour['email']):
                return jsonify({"erreur": "Format email invalide"}), 400
        
        # Valider le téléphone si présent
        if 'telephone' in mises_a_jour and mises_a_jour['telephone']:
            if not valider_telephone(mises_a_jour['telephone']):
                return jsonify({"erreur": "Numéro de téléphone invalide"}), 400
        
        # Ne pas modifier l'ID ni la date de création
        mises_a_jour.pop('id', None)
        mises_a_jour.pop('date_creation', None)
        
        utilisateur.update(mises_a_jour)
        sauvegarder_donnees(toutes_donnees)
        
        return jsonify({
            "message": "Utilisateur modifié avec succès",
            "utilisateur": utilisateur
        }), 200
    
    except Exception as e:
        print(f"Erreur lors de la modification : {e}")
        return jsonify({"erreur": str(e)}), 500

@app.route('/api/donnees/<int:user_id>', methods=['DELETE'])
def supprimer(user_id):
    """Supprime un utilisateur et ses commentaires"""
    try:
        toutes_donnees = charger_donnees()
        
        # Vérifier que l'utilisateur existe
        utilisateur = next((u for u in toutes_donnees['registre'] if u['id'] == user_id), None)
        if not utilisateur:
            return jsonify({"erreur": "Utilisateur non trouvé"}), 404
        
        # Supprimer l'utilisateur et ses commentaires
        toutes_donnees['registre'] = [u for u in toutes_donnees['registre'] if u['id'] != user_id]
        toutes_donnees['commentaires'] = [c for c in toutes_donnees['commentaires'] if c['user_id'] != user_id]
        
        sauvegarder_donnees(toutes_donnees)
        
        return jsonify({
            "message": f"Utilisateur {user_id} et ses commentaires ont été supprimés"
        }), 200
    
    except Exception as e:
        print(f"Erreur lors de la suppression : {e}")
        return jsonify({"erreur": str(e)}), 500

@app.route('/api/commentaires/<int:user_id>', methods=['GET'])
def obtenir_commentaires(user_id):
    """Retourne les commentaires d'un utilisateur"""
    try:
        toutes_donnees = charger_donnees()
        
        # Vérifier que l'utilisateur existe
        utilisateur = next((u for u in toutes_donnees['registre'] if u['id'] == user_id), None)
        if not utilisateur:
            return jsonify({"erreur": "Utilisateur non trouvé"}), 404
        
        commentaires = [c for c in toutes_donnees['commentaires'] if c['user_id'] == user_id]
        return jsonify({"user_id": user_id, "commentaires": commentaires}), 200
    
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.errorhandler(404)
def page_non_trouvee(error):
    """Gère les erreurs 404"""
    return jsonify({"erreur": "Endpoint non trouvé"}), 404

@app.errorhandler(500)
def erreur_serveur(error):
    """Gère les erreurs 500"""
    return jsonify({"erreur": "Erreur serveur interne"}), 500

if __name__ == '__main__':
    # En production, changez debug=False
    app.run(host='0.0.0.0', port=5000, debug=False)

from flask import Flask, request, jsonify, render_template
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# ====== CONFIGURATION MongoDB ======

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')  # Vérifier la connexion
    db = client['crud_db']
    registre_collection = db['registre']
    commentaires_collection = db['commentaires']
    print("✅ Connecté à MongoDB")
except Exception as e:
    print(f"❌ Erreur de connexion MongoDB : {e}")
    db = None

# ====== UTILITAIRES ======

def valider_email(email):
    """Validation du format email avec regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def valider_telephone(telephone):
    """Validation basique du numéro de téléphone"""
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

def get_next_user_id():
    """Obtient le prochain ID utilisateur"""
    dernier = registre_collection.find_one(sort=[("id", -1)])
    return (dernier['id'] + 1) if dernier else 1

def get_next_comment_id():
    """Obtient le prochain ID commentaire"""
    dernier = commentaires_collection.find_one(sort=[("id", -1)])
    return (dernier['id'] + 1) if dernier else 1

def convertir_objectid(obj):
    """Convertit les ObjectId MongoDB en string pour JSON"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                obj[key] = str(value)
            elif isinstance(value, dict):
                convertir_objectid(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        convertir_objectid(item)
    return obj

# ====== ROUTES ======

@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/submit', methods=['POST'])
def soumettre():
    """Traite la soumission du formulaire HTML"""
    try:
        if db is None:
            return render_template('erreur.html', message="Base de données indisponible"), 500
        
        donnees = nettoyer_donnees(request.form.to_dict())
        requis = ['name', 'prename', 'num', 'mail']
        
        valide, erreur = valider_entree(donnees, requis)
        if not valide:
            return render_template('erreur.html', message=erreur), 400
        
        # Créer le nouvel utilisateur
        nouvel_id = get_next_user_id()
        utilisateur = {
            "id": nouvel_id,
            "nom": donnees['name'],
            "prenom": donnees['prename'],
            "telephone": donnees['num'],
            "email": donnees['mail'],
            "date_creation": datetime.now().isoformat()
        }
        registre_collection.insert_one(utilisateur)
        
        # Créer le commentaire associé
        commentaire = {
            "id": get_next_comment_id(),
            "user_id": nouvel_id,
            "impression": donnees.get('imp', ''),
            "avis": donnees.get('Avis', '')
        }
        commentaires_collection.insert_one(commentaire)
        
        return render_template('succes.html', user_id=nouvel_id)
    
    except Exception as e:
        print(f"Erreur lors de la soumission : {e}")
        return render_template('erreur.html', message="Une erreur est survenue lors de l'enregistrement"), 500

@app.route('/api/donnees', methods=['GET'])
def obtenir_tous():
    """Retourne tous les enregistrements et commentaires"""
    try:
        if db is None:
            return jsonify({"erreur": "Base de données indisponible"}), 500
        
        registre = list(registre_collection.find({}, {'_id': 0}))
        commentaires = list(commentaires_collection.find({}, {'_id': 0}))
        
        return jsonify({
            "registre": registre,
            "commentaires": commentaires
        })
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route('/api/donnees', methods=['POST'])
def creer():
    """Crée un nouvel enregistrement via API"""
    try:
        if db is None:
            return jsonify({"erreur": "Base de données indisponible"}), 500
        
        nouveau = request.get_json()
        if not nouveau:
            return jsonify({"erreur": "Corps de la requête vide"}), 400
        
        nouveau = nettoyer_donnees(nouveau)
        requis = ['nom', 'prenom', 'telephone', 'email']
        
        valide, erreur = valider_entree(nouveau, requis)
        if not valide:
            return jsonify({"erreur": erreur}), 400
        
        nouvel_id = get_next_user_id()
        nouveau['id'] = nouvel_id
        nouveau['date_creation'] = datetime.now().isoformat()
        
        registre_collection.insert_one(nouveau)
        
        # Créer le commentaire associé
        commentaire = {
            "id": get_next_comment_id(),
            "user_id": nouvel_id,
            "impression": nouveau.get("impression", ""),
            "avis": nouveau.get("avis", "")
        }
        commentaires_collection.insert_one(commentaire)
        
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
        if db is None:
            return jsonify({"erreur": "Base de données indisponible"}), 500
        
        utilisateur = registre_collection.find_one({"id": user_id}, {'_id': 0})
        if not utilisateur:
            return jsonify({"erreur": "Utilisateur non trouvé"}), 404
        return jsonify(utilisateur)
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route('/api/donnees/<int:user_id>', methods=['PUT'])
def modifier(user_id):
    """Modifie un utilisateur existant"""
    try:
        if db is None:
            return jsonify({"erreur": "Base de données indisponible"}), 500
        
        utilisateur = registre_collection.find_one({"id": user_id})
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
        mises_a_jour.pop('_id', None)
        
        registre_collection.update_one({"id": user_id}, {"$set": mises_a_jour})
        utilisateur_mis_a_jour = registre_collection.find_one({"id": user_id}, {'_id': 0})
        
        return jsonify({
            "message": "Utilisateur modifié avec succès",
            "utilisateur": utilisateur_mis_a_jour
        }), 200
    
    except Exception as e:
        print(f"Erreur lors de la modification : {e}")
        return jsonify({"erreur": str(e)}), 500

@app.route('/api/donnees/<int:user_id>', methods=['DELETE'])
def supprimer(user_id):
    """Supprime un utilisateur et ses commentaires"""
    try:
        if db is None:
            return jsonify({"erreur": "Base de données indisponible"}), 500
        
        utilisateur = registre_collection.find_one({"id": user_id})
        if not utilisateur:
            return jsonify({"erreur": "Utilisateur non trouvé"}), 404
        
        # Supprimer l'utilisateur et ses commentaires
        registre_collection.delete_one({"id": user_id})
        commentaires_collection.delete_many({"user_id": user_id})
        
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
        if db is None:
            return jsonify({"erreur": "Base de données indisponible"}), 500
        
        utilisateur = registre_collection.find_one({"id": user_id})
        if not utilisateur:
            return jsonify({"erreur": "Utilisateur non trouvé"}), 404
        
        commentaires = list(commentaires_collection.find({"user_id": user_id}, {'_id': 0}))
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
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

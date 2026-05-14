from flask import Flask, request, jsonify
app = Flask(__name__)

# Notre "Base de données" temporaire
registre = []
commentaires = []

@app.route('/')
def index():
    return """
    <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { min-height: 100vh; background-color: #1a1f2e; color: #c9d1d9; font-family: sans-serif; }
    </style>
    <div style='font-family: sans-serif; text-align: center; padding: 30px; min-height: 100vh; background-color: #1e2030; margin: 0;'>
    <h1 style='color: #2c3e50;'><b>Serveur de James opérationnel</b></h1>
    <p style='font-size: 1.2em;'>allez sur
    <a href='/api/data' style='color: #3498db; text-decoration: none; font-weight: bold;'>/api/data</a> pour voir le registre.</p>
    <form action="/submit" method="post">
    <label for="name">nom</label>
    <input type="text" id="name" name="name" style="color: black;" placeholder="VOTRE NOM" required><br><br>
    <label for="prename">prenom</label>
    <input type="text" id="prename" name="prename" style="color: black;" placeholder="VOTRE PRENOM" required><br><br>
    <label for="num">numero</label>
    <input type="tel" id="num" name="num" style="color: black;" placeholder="VOTRE NUMERO DE TELEPHONE" required><br><br>
    <label for="imp">impression</label>
    <input type="text" id="imp" name="imp" style="color: black;" placeholder="VOTRE IMPRESSION ICI"><br><br>
    <label for="Avis">avis</label>
    <input type="text" id="Avis" name="Avis" style="color: black;" placeholder="VOTRE AVIS ICI"><br><br>
    <label for="mail">e-mail</label>
    <input type="email" id="mail" name="mail" style="color: black;" placeholder="adresse mail nam@gmail.com"><br><br>
    <button type="submit" style="color: blue;">ENVOYER</button><br><br>
    <button type="reset" style="color: blue;">ANNULER</button>
    </form>
    <hr style='border: 0; border-top: 1.5px solid #eee; margin: 20px 0;'>
    <p style='background-color: #1877f2; padding: 10px; border-radius: 5px; display: inline-block;'>
    <a href='https://www.facebook.com/walter.jeen.2025' style='color: white; text-decoration: none; font-weight: bold;'>devenons amis sur facebook!</a>
    </p>
    </div>"""

# ROUTE FORMULAIRE
@app.route('/submit', methods=['POST'])
def submit():
    nom = request.form.get('name')
    prenom = request.form.get('prename')
    telephone = request.form.get('num')
    impression = request.form.get('imp')
    avis = request.form.get('Avis')
    email = request.form.get('mail')
    new_id = len(registre) + 1
    registre.append({
        "ID": new_id,
        "nom": nom,
        "prenom": prenom,
        "telephone": telephone,
        "email": email
    })
    commentaires.append({
        "id": len(commentaires) + 1,
        "new_id": new_id,
        "impression": impression,
        "avis": avis
    })
    return """
    <style>
    body { background-color: #1a1f2e; color: #c9d1d9; font-family: sans-serif; text-align: center; padding: 50px; }
    a { color: #3498db; }
    </style>
    <h2>données enregistrées avec succès</h2><br>
    <a href="/" style='color: #3498db; text-decoration: none; font-weight: bold;'>retour</a>
    <a href="/api/data" style='color: #3498db; text-decoration: none; font-weight: bold;'>voir le registre</a>"""

# READ : Voir tout
@app.route('/api/data', methods=['GET'])
def get_all():
    return jsonify({"registre": registre, "commentaires": commentaires})

# CREATE : Ajouter (via un outil comme Postman ou Insomnia)
@app.route('/api/data', methods=['POST'])
def create():
    nouveau = request.get_json()
    new_id = len(registre) + 1
    nouveau['id'] = new_id
    registre.append(nouveau)
    commentaires.append({
        "id": len(commentaires) + 1,
        "new_id": nouveau['id'],
        "impression": nouveau.get("impression"),
        "avis": nouveau.get("avis")
    })
    return jsonify({"message": "données ajoutées avec succès et merci pour vos commentaires"}), 201

if __name__ == '__main__':
    # host='0.0.0.0' est INDISPENSABLE pour être vu par les autres machines
    app.run(host='0.0.0.0', port=5000, debug=True)

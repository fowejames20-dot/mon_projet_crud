from flask import Flask, request, jsonify
app =Flask(__name__)

# Notre "Base de données" temporaire
registre = []
commentaires = []

@app.route('/')
def index():
    return """
    <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { min-height: 100vh; background-color: #1a1f2e; color: #c9d1d9; }
    </style>
    <div style='font-family: sans-seriif;text-align: center; padding: 30px; min-height: 100vh; background-color #1e2030; margin: o;'>
    <h1 style='color: #2c3e50;'><b>Serveur de James opérationnel </b></h1>
    <p style='font-size: 1.2em;'>allez sur
    <a href='/api/data' style='color: #3498db; text-decoration: none; font-weight: bolt;'>/api/data</a>pour voir le registre.</p>
    <hr style='border: 0; border-top: 1.5px solid #eee; margin: 20px 0;'>
    <p style='background-color: #1877f2; padding: 10px;border-radius: 5px; display: inline-block;'>
    <a href='https://www.facebook.com/walter.jeen.2025' style='color: white; text-decoration: none; front-weight: bolt;'> devenons amis sur facebook!
    </a>
    </p>
    </div>"""

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
    commentaires.append(
    {"id": len(commentaires) + 1,
    "new_id": nouveau['id'],
    "impression": nouveau.get("impression"),
    "avis": nouveau.get("avis")
    })

    return jsonify({"message": "données  ajoutées avec succès et merçi pour vos commentaires"}), 201
if __name__ == '__main__':

# host='0.0.0.0' est INDISPENSABLE pour être vu par les autres machines
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

DB = "leadcloser.db"

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeadCloser</title>

<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f7fb;
    color: #172033;
}

header {
    background: #111827;
    color: white;
    padding: 25px;
}

.container {
    max-width: 1100px;
    margin: auto;
    padding: 20px;
}

h1 {
    margin: 0;
}

.card {
    background: white;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 3px 15px rgba(0,0,0,.06);
}

input, select, textarea, button {
    width: 100%;
    padding: 12px;
    margin-top: 8px;
    margin-bottom: 12px;
    box-sizing: border-box;
    border-radius: 8px;
    border: 1px solid #d1d5db;
}

button {
    background: #111827;
    color: white;
    cursor: pointer;
    border: none;
}

.lead {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 15px;
    margin-top: 12px;
}

.badge {
    display: inline-block;
    padding: 5px 9px;
    border-radius: 20px;
    background: #eef2ff;
}

.grid {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 20px;
}

@media(max-width:700px) {
    .grid {
        grid-template-columns: 1fr;
    }
}

.message {
    background: #f3f4f6;
    padding: 12px;
    border-radius: 8px;
    margin-top: 8px;
}
</style>
</head>

<body>

<header>
<div class="container">
<h1>LeadCloser</h1>
<p>Gestão inteligente de leads para imobiliárias</p>
</div>
</header>

<div class="container">

<div class="grid">

<div>

<div class="card">
<h2>Novo Lead</h2>

<form method="POST" action="/add">

<input name="name" placeholder="Nome do cliente" required>

<input name="phone" placeholder="WhatsApp">

<input name="property" placeholder="Imóvel de interesse">

<textarea name="notes" placeholder="Observações"></textarea>

<button type="submit">
Adicionar Lead
</button>

</form>
</div>

<div class="card">
<h3>O objetivo</h3>

<p>
Não deixar clientes interessados serem esquecidos.
</p>

<p>
O LeadCloser organiza os leads e ajuda o corretor a saber quem precisa de follow-up.
</p>

</div>

</div>

<div class="card">

<h2>Pipeline de Leads</h2>

{% for lead in leads %}

<div class="lead">

<strong>{{ lead["name"] }}</strong>

<p>
📱 {{ lead["phone"] or "WhatsApp não informado" }}
</p>

<p>
🏠 {{ lead["property"] or "Imóvel não informado" }}
</p>

<p>
<span class="badge">
{{ lead["stage"] }}
</span>
</p>

<p>
<strong>Próximo follow-up:</strong>
{{ lead["next_followup"] or "Não definido" }}
</p>

<form method="POST" action="/stage/{{ lead['id'] }}">

<select name="stage">

{% for stage in [
"Novo",
"Contactado",
"Interessado",
"Visita agendada",
"Proposta",
"Fechado",
"Perdido"
] %}

<option
{% if lead["stage"] == stage %}selected{% endif %}
>
{{ stage }}
</option>

{% endfor %}

</select>

<button type="submit">
Atualizar etapa
</button>

</form>

<div class="message">

<strong>Mensagem sugerida:</strong>

<br><br>

Olá, {{ lead["name"] }}! Tudo bem?

Vi que você demonstrou interesse em
{{ lead["property"] or "um imóvel" }}.

Posso te ajudar com mais informações e algumas opções que podem combinar com o que você procura?

</div>
<a href="https://wa.me/{{ lead['phone']|replace(' ', '')|replace('+', '')|replace('-', '')|replace('(', '')|replace(')', '') }}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:12px; border-radius:8px; text-decoration:none; margin-top:12px;">
    💬 Falar no WhatsApp
</a>
</div>

{% else %}

<p>
Ainda não existem leads cadastrados.
</p>

{% endfor %}

</div>

</div>

</div>

</body>
</html>
"""


def database():

    connection = sqlite3.connect(DB)

    connection.row_factory = sqlite3.Row

    return connection


def initialize():

    connection = database()

    connection.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        property TEXT,
        stage TEXT DEFAULT 'Novo',
        next_followup TEXT,
        notes TEXT
    )
    """)

    connection.commit()

    connection.close()


@app.route("/")
def home():

    connection = database()

    leads = connection.execute(
        "SELECT * FROM leads ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template_string(
        HTML,
        leads=leads
    )


@app.post("/add")
def add_lead():

    name = request.form["name"]

    phone = request.form.get("phone")

    property_name = request.form.get("property")

    notes = request.form.get("notes")

    followup = (
        datetime.now() + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    connection = database()

    connection.execute(
        """
        INSERT INTO leads
        (name, phone, property, stage, next_followup, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            phone,
            property_name,
            "Novo",
            followup,
            notes
        )
    )

    connection.commit()

    connection.close()

    return redirect("/")


@app.post("/stage/<int:lead_id>")
def update_stage(lead_id):

    stage = request.form["stage"]

    connection = database()

    connection.execute(
        """
        UPDATE leads
        SET stage = ?
        WHERE id = ?
        """,
        (stage, lead_id)
    )

    connection.commit()

    connection.close()

    return redirect("/")


initialize()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
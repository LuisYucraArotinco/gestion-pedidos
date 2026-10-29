from flask import Flask, render_template, request, jsonify, Response
from analizador import compilar, ejecutar_pruebas, GRAMATICA

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.post("/api/compilar")
def api_compilar():
    datos = request.get_json(silent=True) or {}
    codigo = datos.get("codigo", "")
    return jsonify(compilar(codigo))


@app.get("/api/pruebas")
def api_pruebas():
    return jsonify(ejecutar_pruebas())


@app.get("/api/gramatica")
def api_gramatica():
    return jsonify({"gramatica": GRAMATICA})


@app.get("/api/exportar-pruebas")
def exportar_pruebas():
    resultados = ejecutar_pruebas()
    lineas = [
        "caso,entrada,esperado,obtenido,correcto,tiempo_ms"
    ]

    for r in resultados["casos"]:
        entrada = '"' + r["entrada"].replace('"', '""') + '"'
        lineas.append(
            f'{r["nombre"]},{entrada},{r["esperado"]},'
            f'{r["obtenido"]},{r["correcto"]},{r["tiempo_ms"]}'
        )

    contenido = "\n".join(lineas)

    return Response(
        contenido,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=pruebas_compilador.csv"
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
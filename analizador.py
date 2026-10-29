import time
import re

GRAMATICA = """PROGRAMA       -> PEDIDO
PEDIDO         -> "PEDIDO" "cliente" "=" IDENTIFICADOR
                  "producto" "=" IDENTIFICADOR
                  "cantidad" "=" NUMERO ";"

IDENTIFICADOR  -> LETRA (LETRA | DIGITO | "_")*
NUMERO         -> DIGITO+
"""


def analizar_lexico(codigo):
    tokens = []
    errores = []
    i = 0
    linea = 1
    columna = 1

    palabras = {
        "PEDIDO": "PALABRA_PEDIDO",
        "cliente": "PALABRA_CLIENTE",
        "producto": "PALABRA_PRODUCTO",
        "cantidad": "PALABRA_CANTIDAD"
    }

    while i < len(codigo):
        c = codigo[i]

        if c in " \t\r":
            i += 1
            columna += 1
            continue

        if c == "\n":
            i += 1
            linea += 1
            columna = 1
            continue

        inicio_columna = columna

        if c.isalpha():
            inicio = i

            while i < len(codigo) and (
                codigo[i].isalnum() or codigo[i] == "_"
            ):
                i += 1
                columna += 1

            lexema = codigo[inicio:i]

            if lexema in palabras:
                tipo = palabras[lexema]
            elif re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", lexema):
                tipo = "IDENTIFICADOR"
            else:
                errores.append(
                    f"Línea {linea}, columna {inicio_columna}: "
                    f"identificador inválido '{lexema}'."
                )
                continue

            tokens.append({
                "tipo": tipo,
                "lexema": lexema,
                "linea": linea,
                "columna": inicio_columna
            })
            continue

        if c.isdigit():
            inicio = i

            while i < len(codigo) and codigo[i].isdigit():
                i += 1
                columna += 1

            tokens.append({
                "tipo": "NUMERO",
                "lexema": codigo[inicio:i],
                "linea": linea,
                "columna": inicio_columna
            })
            continue

        simbolos = {
            "=": "IGUAL",
            ";": "PUNTO_COMA"
        }

        if c in simbolos:
            tokens.append({
                "tipo": simbolos[c],
                "lexema": c,
                "linea": linea,
                "columna": inicio_columna
            })
            i += 1
            columna += 1
            continue

        errores.append(
            f"Línea {linea}, columna {columna}: "
            f"carácter no reconocido '{c}'."
        )
        i += 1
        columna += 1

    return tokens, errores


def analizar_sintactico(tokens):
    esperados = [
        ("PALABRA_PEDIDO", "PEDIDO"),
        ("PALABRA_CLIENTE", "cliente"),
        ("IGUAL", "="),
        ("IDENTIFICADOR", None),
        ("PALABRA_PRODUCTO", "producto"),
        ("IGUAL", "="),
        ("IDENTIFICADOR", None),
        ("PALABRA_CANTIDAD", "cantidad"),
        ("IGUAL", "="),
        ("NUMERO", None),
        ("PUNTO_COMA", ";")
    ]

    if not tokens:
        return False, "No se encontraron tokens.", None

    for posicion, (tipo, lexema) in enumerate(esperados):
        if posicion >= len(tokens):
            return (
                False,
                f"Error sintáctico: falta {lexema or tipo} "
                f"en la posición {posicion + 1}.",
                None
            )

        token = tokens[posicion]

        if token["tipo"] != tipo:
            return (
                False,
                f"Error sintáctico en línea {token['linea']}, "
                f"columna {token['columna']}: se esperaba "
                f"{lexema or tipo}, pero llegó '{token['lexema']}'.",
                None
            )

        if lexema is not None and token["lexema"] != lexema:
            return (
                False,
                f"Se esperaba '{lexema}', pero llegó "
                f"'{token['lexema']}'.",
                None
            )

    if len(tokens) > len(esperados):
        extra = tokens[len(esperados)]

        return (
            False,
            f"Sobra el elemento '{extra['lexema']}' "
            "después de la instrucción.",
            None
        )

    pedido = {
        "cliente": tokens[3]["lexema"],
        "producto": tokens[6]["lexema"],
        "cantidad": int(tokens[9]["lexema"])
    }

    arbol = [
        "PEDIDO",
        "├── Palabra reservada: PEDIDO",
        f"├── cliente: {pedido['cliente']}",
        f"├── producto: {pedido['producto']}",
        f"└── cantidad: {pedido['cantidad']}"
    ]

    return True, "La estructura sintáctica es correcta.", {
        "pedido": pedido,
        "arbol": arbol
    }


def compilar(codigo):
    inicio = time.perf_counter()

    tokens, errores_lexicos = analizar_lexico(codigo)

    resultado = {
        "valido": False,
        "estado": "RECHAZADO",
        "tiempo_ms": 0,
        "tokens": tokens,
        "errores_lexicos": errores_lexicos,
        "sintaxis": {
            "correcto": False,
            "mensaje": "No ejecutado."
        },
        "semantica": {
            "correcto": False,
            "mensaje": "No ejecutado."
        },
        "arbol": [],
        "tabla_simbolos": [],
        "codigo_intermedio": [],
        "diagnosticos": []
    }

    if errores_lexicos:
        resultado["diagnosticos"].extend(errores_lexicos)
        resultado["sintaxis"]["mensaje"] = (
            "No se ejecutó por los errores léxicos."
        )
    else:
        correcto, mensaje, datos = analizar_sintactico(tokens)

        resultado["sintaxis"] = {
            "correcto": correcto,
            "mensaje": mensaje
        }

        if not correcto:
            resultado["diagnosticos"].append(mensaje)
        else:
            pedido = datos["pedido"]
            resultado["arbol"] = datos["arbol"]

            if pedido["cantidad"] <= 0:
                resultado["semantica"] = {
                    "correcto": False,
                    "mensaje": "La cantidad debe ser mayor que cero."
                }
                resultado["diagnosticos"].append(
                    resultado["semantica"]["mensaje"]
                )
            else:
                resultado["semantica"] = {
                    "correcto": True,
                    "mensaje": "La cantidad es mayor que cero."
                }

                resultado["tabla_simbolos"] = [
                    {
                        "nombre": "cliente",
                        "tipo": "IDENTIFICADOR",
                        "valor": pedido["cliente"]
                    },
                    {
                        "nombre": "producto",
                        "tipo": "IDENTIFICADOR",
                        "valor": pedido["producto"]
                    },
                    {
                        "nombre": "cantidad",
                        "tipo": "ENTERO",
                        "valor": str(pedido["cantidad"])
                    }
                ]

                resultado["codigo_intermedio"] = [
                    f'cliente := "{pedido["cliente"]}"',
                    f'producto := "{pedido["producto"]}"',
                    f'cantidad := {pedido["cantidad"]}',
                    "REGISTRAR_PEDIDO(cliente, producto, cantidad)"
                ]

                resultado["valido"] = True
                resultado["estado"] = "COMPILACIÓN EXITOSA"
                resultado["diagnosticos"].append(
                    "La instrucción pasó las tres etapas de análisis."
                )

    resultado["tiempo_ms"] = round(
        (time.perf_counter() - inicio) * 1000, 3
    )

    return resultado


def ejecutar_pruebas():
    casos = [
        ("CP01", "PEDIDO cliente=CLI_01 producto=PROD_15 cantidad=3;", True),
        ("CP02", "PEDIDO cliente=CLI_01 producto=PROD_15 cantidad=0;", False),
        ("CP03", "PEDIDO cliente=CLI_01 producto=PROD_15 cantidad=3", False),
        ("CP04", "PEDIDO cliente=CLI_01 producto=PROD_15;", False),
        ("CP05", "PEDIDO producto=PROD_15 cliente=CLI_01 cantidad=3;", False),
        ("CP06", "PEDIDO cliente=CLI-01 producto=PROD_15 cantidad=3;", False),
        ("CP07", "PEDIDO cliente=CLI_01 producto=PROD_15 cantidad=-2;", False),
        ("CP08", "PEDIDO cliente= producto=PROD_15 cantidad=3;", False),
        ("CP09", "PEDIDO cliente=CLI_01 producto=PROD_15 cantidad=2.5;", False),
        ("CP10", "PEDIDO cliente CLI_01 producto=PROD_15 cantidad=3;", False)
    ]

    resultados = []
    aciertos = 0

    for nombre, entrada, esperado in casos:
        r = compilar(entrada)
        obtenido = r["valido"]
        coincide = esperado == obtenido

        if coincide:
            aciertos += 1

        resultados.append({
            "nombre": nombre,
            "entrada": entrada,
            "esperado": "VÁLIDO" if esperado else "INVÁLIDO",
            "obtenido": "VÁLIDO" if obtenido else "INVÁLIDO",
            "correcto": "Sí" if coincide else "No",
            "tiempo_ms": r["tiempo_ms"],
            "detalle": r["diagnosticos"][0]
            if r["diagnosticos"] else r["estado"]
        })

    return {
        "total": len(resultados),
        "aciertos": aciertos,
        "precision": round(aciertos / len(resultados) * 100, 1),
        "casos": resultados
    }
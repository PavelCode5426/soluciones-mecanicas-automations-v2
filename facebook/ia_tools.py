from facebook import services


def get_products_information(query: str) -> str:
    try:
        products = services.SolucionesMecanicasAPIServices.get_all_products(query)
        response = "Informacion de todos los productos disponibles en la tienda:\n\n"

        for product in products:
            info = f"""
        ### Información del producto

        - **Producto:** {product['name']}
        - **Disponibilidad:** {product['quantity']}
        - **Categoría del producto:** {product['category']['name']}
        - **Marca del producto:** {product['brand']['name']}
        - **Precio unitario:** CUP {product['unit_price']}
        - **Contenido neto:** {product['net_content']}
        ---
        """
            response += info

        return response
    except Exception as e:
        return "Lo siento, tuve un problema al consultar los productos. Por favor, intenta más tarde."


def get_categories_information():
    try:
        categories = services.SolucionesMecanicasAPIServices.get_all_categories()
        response = "Estas son todas las categorias disponibles: "

        for category in categories:
            response += category['name'] + ","

        return response
    except Exception as e:
        return "Lo siento, tuve un problema al consultar los productos. Por favor, intenta más tarde."

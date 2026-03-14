from llama_index.core import Document, VectorStoreIndex, SummaryIndex, DocumentSummaryIndex, SimpleKeywordTableIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.query_engine import RouterQueryEngine, SubQuestionQueryEngine
from llama_index.core.selectors import PydanticMultiSelector
from llama_index.core.tools import QueryEngineTool

import services.stores as services


def get_products_information(query: str) -> str:
    products = services.SolucionesMecanicasAPIServices.get_all_products(query)
    product_docs = []
    for product in products:
        text = f"""
        - **Producto:** {product['name']}
        - **Disponibilidad:** {product['quantity']}
        - **Categoría del producto:** {product['category']['name']}
        - **Marca del producto:** {product['brand']['name']}
        - **Precio unitario:** CUP {product['unit_price']}
        - **Contenido neto:** {product['net_content']}
        ---
        """
        product_docs.append(Document(text=text, metadata=product))

    splitter = SentenceSplitter(chunk_size=100)
    product_vector_index = VectorStoreIndex(product_docs)
    product_summary_index = SummaryIndex(product_docs)
    product_summary_index = DocumentSummaryIndex(product_docs)
    product_keyword_index = SimpleKeywordTableIndex(product_docs)

    query_engine = RouterQueryEngine.from_defaults(
        selector=PydanticMultiSelector.from_defaults(), query_engine_tools=[
            QueryEngineTool.from_defaults(product_vector_index.as_query_engine()),
            QueryEngineTool.from_defaults(product_summary_index.as_query_engine()),
            QueryEngineTool.from_defaults(product_keyword_index.as_query_engine()),
        ]
    )

    subquestion = SubQuestionQueryEngine.from_defaults(query_engine_tools=[
        QueryEngineTool.from_defaults(product_vector_index.as_query_engine()),
        QueryEngineTool.from_defaults(product_summary_index.as_query_engine()),
        QueryEngineTool.from_defaults(product_keyword_index.as_query_engine(), ),
    ])

    QueryEngineTool.from_defaults(query_engine)
    QueryEngineTool.from_defaults(subquestion)


def get_categories_information():
    try:
        categories = services.SolucionesMecanicasAPIServices.get_all_categories()
        response = "Estas son todas las categorias disponibles: "

        for category in categories:
            response += category['name'] + ","

        return response
    except Exception as e:
        return "Lo siento, tuve un problema al consultar los productos. Por favor, intenta más tarde."

"""Create or update the shared Azure AI Search index used by AzureSearchStore."""

import argparse

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from app.config import get_settings


def create_index(endpoint: str, name: str, key: str = "") -> None:
    credential = AzureKeyCredential(key) if key else DefaultAzureCredential()
    client = SearchIndexClient(endpoint=endpoint, credential=credential)
    index = SearchIndex(
        name=name,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="doc_id", type=SearchFieldDataType.String, filterable=True),
            SearchField(name="text", type=SearchFieldDataType.String, searchable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="hnsw-profile",
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
            profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw")],
        ),
    )
    client.create_or_update_index(index)


if __name__ == "__main__":
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default=settings.azure_search_endpoint, required=False)
    parser.add_argument("--index", default=settings.azure_search_index)
    parser.add_argument("--key", default=settings.azure_search_key)
    args = parser.parse_args()
    if not args.endpoint:
        parser.error("--endpoint or AZURE_SEARCH_ENDPOINT is required")
    create_index(args.endpoint, args.index, args.key)
    print(f"Index {args.index} created or updated")

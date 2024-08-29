# Azure AI Contents Generation

## Introduction

In this demo, we will show you some marketing contents generation use case with Azure AI.

## Design

- Prepare various dataset(pdf, video, image, text)
- Preprocess each data type.
- Generate marketing content based on user's request(request is defined as prompt for GPT model)

## Prerequisites

- An Azure subscription. If you don't have an Azure subscription, [create a free account](https://aka.ms/AMLFree) before you begin.
- Azure AI Search resource, resource can be created via Azure Portal. [Read here](hhttps://learn.microsoft.com/eu-es/azure/search/search-create-service-portal)
- Azure OpenAI Service resource and model, recource can be created via Azure Portal. Model can be deployed via Azure OpenAI Studio. [Read here](https://learn.microsoft.com/eu-es/azure/ai-services/openai/how-to/create-resource?pivots=web-portal)
- Azure AI Vision resource, resource can be created via Azure Portal as multi-service resource for Azure AI services. [Read here](https://learn.microsoft.com/en-us/azure/ai-services/multi-service-resource?tabs=linux&pivots=azportal)
- Azure Storage Account and blob container, these can be created via Azure Portal. [Read here](https://learn.microsoft.com/eu-es/azure/storage/blobs/blob-containers-portal)
- Azure AI Document Intelligence resource, , recource can be created via Azure Portal. [Read here](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/use-sdk-rest-api?view=doc-intel-4.0.0&tabs=windows&pivots=programming-language-python)
- Once you have created above resources, you need to set `.env` and define the following variables. These variables can be found in Azure Portal and Azure OpenAI Studio.
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_DEPLOYMENT`
  - `AZURE_OPENAI_API_VERSION`
  - `AZURE_SEARCH_ENDPOINT`
  - `AZURE_SEARCH_ADMIN_KEY`
  - `AZURE_AI_VISION_ENDPOINT`
  - `AZURE_AI_VISION_API_KEY`
  - `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
  - `AZURE_DOCUMENT_INTELLIGENCE_KEY`
  - `BLOB_CONNECTION_STRING`
  - `BLOB_CONTAINER_NAME`

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.

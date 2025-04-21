This file is a merged representation of a subset of the codebase, containing specifically included files, combined into a single document by Repomix.
The content has been processed where security check has been disabled.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: docs/docs/**
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Security check has been disabled - content may contain sensitive information
- Files are sorted by Git change count (files with more changes are at the bottom)

## Additional Info

# Directory Structure
```
docs/
  docs/
    aggregate-functions/
      _category_.json
      aggregate-functions.md
      llm-first.md
      llm-last.md
      llm-reduce-json.md
      llm-reduce.md
      llm-rerank.md
    getting-started/
      _category_.json
      azure.md
      getting-started.md
      ollama.md
      openai.md
    resource-management/
      _category_.json
      api-keys.md
      models.md
      prompts.md
      resource-management.md
    scalar-functions/
      _category_.json
      llm-complete-json.md
      llm-complete.md
      llm-embedding.md
      llm-filter.md
      scalar-functions.md
    faq.mdx
    hybrid-search.md
    what-is-flockmtl.md
```

# Files

## File: docs/docs/aggregate-functions/_category_.json
````json
{
  "label": "Aggregate Functions",
  "position": 5,
  "link": {
    "id": "aggregate-functions",
    "type": "doc"
  }
}
````

## File: docs/docs/aggregate-functions/aggregate-functions.md
````markdown
# Aggregate Functions

Aggregate functions in FlockMTL perform operations on groups of rows, returning a single result for each group. They're particularly useful for summarizing, ranking, and reordering data, often used with the `GROUP BY` clause in SQL queries. Leveraging language models, these functions enable advanced tasks like summarization, ranking, and relevance-based filtering, enhancing data analysis and NLP capabilities.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. Available Aggregate Functions

FlockMTL offers several powerful aggregate functions:

1. [**`llm_reduce`**](/docs/aggregate-functions/llm-reduce): Aggregates a group of rows using a language model, typically for summarization or text consolidation.

   - **Example Use Cases**: Summarizing documents, aggregating product descriptions.

2. [**`llm_reduce_json`**](/docs/aggregate-functions/llm-reduce): Aggregates multiple rows into a single JSON output using a language model, ideal for tasks like summarization or consolidating text across multiple features.

   - **Example Use Cases**: Extracting key insights and sentiment from reviews, generating a summary with multiple attributes like themes and tone from survey responses.

3. [**`llm_rerank`**](/docs/aggregate-functions/llm-rerank): Reorders a list of rows based on relevance to a prompt using a sliding window mechanism.
   - **Example Use Cases**: Reranking search results, adjusting document or product rankings.

4. [**`llm_first`**](/docs/aggregate-functions/llm-first): Returns the most relevant item from a group based on a prompt.

   - **Example Use Cases**: Selecting the top-ranked document, finding the most relevant product.

5. [**`llm_last`**](/docs/aggregate-functions/llm-last): Returns the least relevant item from a group based on a prompt.

   - **Example Use Cases**: Finding the least relevant document, selecting the least important product.

## 2. How Aggregate Functions Work

Aggregate functions process groups of rows defined by a `GROUP BY` clause. They apply language models to the grouped data, generating a single result per group. This result can be a summary, a ranking, or another output defined by the prompt.

## 3. When to Use Aggregate Functions

- **Summarization**: Use `llm_reduce` to consolidate multiple rows.
- **Ranking**: Use `llm_first`, `llm_last`, or `llm_rerank` to reorder rows based on relevance.
- **Data Aggregation**: Use these functions to process and summarize grouped data, especially for text-based tasks.
````

## File: docs/docs/aggregate-functions/llm-first.md
````markdown
---
title: llm_first
sidebar_position: 4
---

# llm_first Aggregate Function

The `llm_first` function is used to extract the first matching result that satisfies a condition defined by a model's prompt and column data. It operates across rows, typically combined with a `GROUP BY` clause, to return the first relevant row for each group.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. **Usage Examples**

### 1.1. **Example without `GROUP BY`**

Retrieve the first relevant product feature across all rows:

```sql
SELECT llm_first(
    {'model_name': 'gpt-4'},
    {'prompt': 'What is the most relevant detail for these products, based on their names and descriptions?'},
    {'product_name': product_name, 'product_description': product_description}
) AS first_product_feature
FROM products;
```

**Description**: This query returns the first relevant feature from all product descriptions and product names, based on the provided prompt.

### 1.2. **Example with `GROUP BY`**

Retrieve the first relevant product feature for each product category:

```sql
SELECT category,
       llm_first(
           {'model_name': 'gpt-4'},
           {'prompt': 'What is the most relevant detail for these products, based on their names and descriptions?'},
           {'product_name': product_name, 'product_description': product_description}
       ) AS first_product_feature
FROM products
GROUP BY category;
```

**Description**: The query groups the products by category and returns the first relevant feature for each group.

### 1.3. **Using a Named Prompt with `GROUP BY`**

Use a reusable prompt, such as "first-relevant-detail", to extract the first relevant feature for each product category:

```sql
SELECT category,
       llm_first(
           {'model_name': 'gpt-4', 'secret_name': 'product_key'},
           {'prompt_name': 'first-relevant-detail', 'version': 1},
           {'product_name': product_name, 'product_description': product_description}
       ) AS first_product_feature
FROM products
GROUP BY category;
```

**Description**: This example leverages a named prompt (`first-relevant-detail`) to extract the first relevant feature for each product category. The query groups the results by category.

### 1.4. **Advanced Example with Multiple Columns and `GROUP BY`**

Retrieve the first relevant feature for products grouped by category, using both the product name and description:

```sql
WITH product_info AS (
    SELECT category, product_name, product_description
    FROM products
    WHERE category = 'Electronics'
)
SELECT category,
       llm_first(
           {'model_name': 'gpt-4'},
           {'prompt': 'What is the most relevant detail for these products, based on their names and descriptions?'},
           {'product_name': product_name, 'product_description': product_description}
       ) AS first_product_feature
FROM product_info
GROUP BY category;
```

**Description**: This query extracts the first relevant feature from both the `product_name` and `product_description` columns, grouped by product category (in this case, electronics).

## 2. **Input Parameters**

### 2.1 **Model Configuration**

- **Parameter**: `model_name` and `secret_name`

#### 2.1.1 Model Selection

- **Description**: Specifies the model used for text generation.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4' }
  ```

#### 2.1.2 Model Selection with Secret

- **Description**: Specifies the model along with the secret name to be used for authentication when accessing the model.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4', 'secret_name': 'your_secret_name' }
  ```

### 2.2. **Prompt Configuration**

Two types of prompts can be used:

1. **Inline Prompt**

   - Directly provides the prompt in the query.
   - **Example**:
     ```sql
     {'prompt': 'What is the most relevant detail for these products, based on their names and descriptions?'}
     ```

2. **Named Prompt**

   - Refers to a pre-configured prompt by name.
   - **Example**:
     ```sql
     {'prompt_name': 'first-relevant-detail'}
     ```

3. **Named Prompt with Version**
   - Refers to a specific version of a pre-configured prompt.
   - **Example**:
     ```sql
     {'prompt_name': 'first-relevant-detail', 'version': 1}
     ```

### 2.3. **Column Mappings (Optional)**

- **Key**: Column mappings.
- **Purpose**: Maps table columns to prompt variables for input.
- **Example**:
  ```sql
  {'product_name': product_name, 'product_description': product_description}
  ```

## 3. **Output**

- **Type**: JSON object.
- **Behavior**: The function returns a JSON object containing the values of the columns you provided in the input. The structure of the returned JSON will mirror the input columns' values.

**Output Example**:  
For a query that extracts the first relevant feature, the result could look like:

- **Input Rows**:

  - `product_name`: _"Wireless Headphones"_
  - `product_description`: _"High-quality wireless headphones with noise cancellation."_

- **Output JSON**:
  ```json
  {
    "product_name": "Wireless Headphones",
    "product_description": "High-quality wireless headphones with noise cancellation."
  }
  ```

The output contains the values for `product_name` and `product_description` from the first relevant row based on the prompt.
````

## File: docs/docs/aggregate-functions/llm-last.md
````markdown
---
title: llm_last
sidebar_position: 5
---

# llm_last Function

The `llm_last` function is used to extract the least relevant result from a set of rows based on a model's prompt and input columns. It operates over a set of rows, generally combined with a `GROUP BY` clause, to return the least relevant row for each group.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. **Usage Examples**

### 1.1. **Example without `GROUP BY`**

Retrieve the least relevant product feature across all rows:

```sql
SELECT llm_last(
    {'model_name': 'gpt-4'},
    {'prompt': 'What is the least relevant detail for these products, based on their names and descriptions?'},
    {'product_name': product_name, 'product_description': product_description}
) AS last_product_feature
FROM products;
```

This query will return the least relevant feature from all product descriptions and product names.

### 1.2. **Example with `GROUP BY`**

Retrieve the least relevant product feature for each product category:

```sql
SELECT category,
       llm_last(
           {'model_name': 'gpt-4'},
           {'prompt': 'What is the least relevant detail for these products, based on their names and descriptions?'},
           {'product_name': product_name, 'product_description': product_description}
       ) AS last_product_feature
FROM products
GROUP BY category;
```

In this case, the query groups products by category and returns the least relevant feature for each category.

### 1.3. **Using a Named Prompt with `GROUP BY`**

Use a reusable prompt such as "least-relevant-detail" to extract the least relevant feature for each product category:

```sql
SELECT category,
       llm_last(
           {'model_name': 'gpt-4', 'secret_name': 'my_key'},
           {'prompt_name': 'least-relevant-detail', 'version': 1},
           {'product_name': product_name, 'product_description': product_description}
       ) AS last_product_feature
FROM products
GROUP BY category;
```

If the `version` parameter is omitted, the system will use the latest version of the `least-relevant-detail` prompt by default.

### 1.4. **Advanced Example with Multiple Columns and `GROUP BY`**

Retrieve the least relevant feature for products grouped by category, using both the product name and description:

```sql
WITH product_info AS (
    SELECT category, product_name, product_description
    FROM products
    WHERE category = 'Electronics'
)
SELECT category,
       llm_last(
           {'model_name': 'gpt-4'},
           {'prompt': 'What is the least relevant detail for these products, based on their names and descriptions?'},
           {'product_name': product_name, 'product_description': product_description}
       ) AS last_product_feature
FROM product_info
GROUP BY category;
```

This example will extract the least relevant feature from both the product name and description for each product category.

## 2. **Input Parameters**

### 2.1 **Model Configuration**

- **Parameter**: `model_name` and `secret_name`

#### 2.1.1 Model Selection

- **Description**: Specifies the model used for text generation.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4' }
  ```

#### 2.1.2 Model Selection with Secret

- **Description**: Specifies the model along with the secret name to be used for authentication when accessing the model.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4', 'secret_name': 'your_secret_name' }
  ```

### 2.2. **Prompt Configuration**

Two types of prompts can be used:

1. **Inline Prompt**

   - Directly provides the prompt in the query.
   - **Example**:
     ```sql
     {'prompt': 'What is the least relevant detail for these products, based on their names and descriptions?'}
     ```

2. **Named Prompt**

   - Refers to a pre-configured prompt by name.
   - **Example**:
     ```sql
     {'prompt_name': 'least-relevant-detail'}
     ```

3. **Named Prompt with Version**
   - Refers to a specific version of a pre-configured prompt.
   - **Example**:
     ```sql
     {'prompt_name': 'least-relevant-detail', 'version': 1}
     ```

### 2.3. **Column Mappings (Optional)**

- **Key**: Column mappings.
- **Purpose**: Maps table columns to prompt variables for input.
- **Example**:
  ```sql
  {'product_name': product_name, 'product_description': product_description}
  ```

## 3. **Output**

- **Type**: JSON object.
- **Behavior**: The function returns a JSON object containing the values of the columns you provided in the input. The structure of the returned JSON will mirror the input columns' values.

**Output Example**:  
For a query that extracts the least relevant feature, the result could look like:

- **Input Rows**:

  - `product_name`: _"Wireless Headphones"_
  - `product_description`: _"High-quality wireless headphones with noise cancellation."_

- **Output JSON**:
  ```json
  {
    "product_name": "Wireless Headphones",
    "product_description": "High-quality wireless headphones with noise cancellation."
  }
  ```

The output contains the values for `product_name` and `product_description` from the least relevant row based on the prompt.
````

## File: docs/docs/aggregate-functions/llm-reduce-json.md
````markdown
---
title: llm_reduce_json
sidebar_position: 2
---

# llm_reduce_json Aggregate Function

The `llm_reduce_json` function in FlockMTL consolidates multiple rows of text-based results into a single JSON output. It is used in SQL queries with the `GROUP BY` clause to combine multiple values into a summary or reduced form.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. **Usage Examples**

### 1.1. **Example without `GROUP BY`**

Summarize all product descriptions into one single result:

```sql
SELECT llm_reduce_json(
    {'model_name': 'gpt-4'},
    {'prompt': 'Summarize the following product descriptions'},
    {'product_description': product_description}
) AS product_summary
FROM products;
```

**Description**: This example aggregates all product descriptions into one summary. The `llm_reduce_json` function processes the `product_description` column for each row, consolidating the values into a single summarized output.

### 1.2. **Example with `GROUP BY`**

Group the products by category and summarize their descriptions into one for each category:

```sql
SELECT category,
       llm_reduce_json(
           {'model_name': 'gpt-4'},
           {'prompt': 'Summarize the following product descriptions'},
           {'product_description': product_description}
       ) AS summarized_product_info
FROM products
GROUP BY category;
```

**Description**: This query groups the products by category (e.g., electronics, clothing) and summarizes all product descriptions within each category into a single consolidated summary.

### 1.3. **Using a Named Prompt with `GROUP BY`**

Leverage a reusable named prompt for summarization, grouped by category:

```sql
SELECT category,
       llm_reduce_json(
           {'model_name': 'gpt-4', 'secret_name': 'azure_key'},
           {'prompt_name': 'summarizer', 'version': 1},
           {'product_description': product_description}
       ) AS summarized_product_info
FROM products
GROUP BY category;
```

**Description**: This example uses a pre-configured named prompt (`summarizer`) with version `1` to summarize product descriptions. The results are grouped by category, with one summary per category.

### 1.4. **Advanced Example with Multiple Columns and `GROUP BY`**

Summarize product details by category, using both the product name and description:

```sql
WITH product_info AS (
    SELECT category, product_name, product_description
    FROM products
    WHERE category = 'Electronics'
)
SELECT category,
       llm_reduce_json(
           {'model_name': 'gpt-4'},
           {'prompt': 'Summarize the following product details'},
           {'product_name': product_name, 'product_description': product_description}
       ) AS detailed_summary
FROM product_info
GROUP BY category;
```

**Description**: In this advanced example, the query summarizes both the `product_name` and `product_description` columns for products in the "Electronics" category, generating a detailed summary for that category.

## 2. **Input Parameters**

### 2.1 **Model Configuration**

- **Parameter**: `model_name` and `secret_name`

#### 2.1.1 Model Selection

- **Description**: Specifies the model used for text generation.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4' }
  ```

#### 2.1.2 Model Selection with Secret

- **Description**: Specifies the model along with the secret name to be used for authentication when accessing the model.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4', 'secret_name': 'your_secret_name' }
  ```

### 2.2. **Prompt Configuration**

Two types of prompts can be used:

1. **Inline Prompt**

   - Directly provides the prompt in the query.
   - **Example**:
     ```sql
     {'prompt': 'Summarize the following product descriptions'}
     ```

2. **Named Prompt**

   - Refers to a pre-configured prompt by name.
   - **Example**:
     ```sql
     {'prompt_name': 'summarizer'}
     ```

3. **Named Prompt with Version**
   - Refers to a specific version of a pre-configured prompt.
   - **Example**:
     ```sql
     {'prompt_name': 'summarizer', 'version': 1}
     ```

### 2.3. **Column Mappings (Optional)**

- **Key**: Column mappings.
- **Purpose**: Maps table columns to prompt variables for input.
- **Example**:
  ```sql
  {'product_name': product_name, 'product_description': product_description}
  ```

## 3. **Output**

- **Type**: Text (string).
- **Behavior**: The function consolidates multiple rows of text into a single output, summarizing or combining the provided data according to the model's response to the prompt.

**Output Example**:  
For a query that aggregates product descriptions, the result could look like:

- **Input Rows**:

  - `product_name`: _"Running Shoes"_
  - `product_name`: _"Wireless Headphones"_
  - `product_name`: _"Smart Watch"_

- **Output**:  
  `"A variety of products including running shoes, wireless headphones, and smart watches, each designed for comfort, convenience, and performance in their respective categories."`
````

## File: docs/docs/aggregate-functions/llm-reduce.md
````markdown
---
title: llm_reduce
sidebar_position: 1
---

# llm_reduce Aggregate Function

The `llm_reduce` function in FlockMTL consolidates multiple rows of text-based results into a single output. It is used in SQL queries with the `GROUP BY` clause to combine multiple values into a summary or reduced form.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. **Usage Examples**

### 1.1. **Example without `GROUP BY`**

Summarize all product descriptions into one single result:

```sql
SELECT llm_reduce(
    {'model_name': 'gpt-4'},
    {'prompt': 'Summarize the following product descriptions'},
    {'product_description': product_description}
) AS product_summary
FROM products;
```

**Description**: This example aggregates all product descriptions into one summary. The `llm_reduce` function processes the `product_description` column for each row, consolidating the values into a single summarized output.

### 1.2. **Example with `GROUP BY`**

Group the products by category and summarize their descriptions into one for each category:

```sql
SELECT category,
       llm_reduce(
           {'model_name': 'gpt-4'},
           {'prompt': 'Summarize the following product descriptions'},
           {'product_description': product_description}
       ) AS summarized_product_info
FROM products
GROUP BY category;
```

**Description**: This query groups the products by category (e.g., electronics, clothing) and summarizes all product descriptions within each category into a single consolidated summary.

### 1.3. **Using a Named Prompt with `GROUP BY`**

Leverage a reusable named prompt for summarization, grouped by category:

```sql
SELECT category,
       llm_reduce(
           {'model_name': 'gpt-4', 'secret_name': 'azure_key'},
           {'prompt_name': 'summarizer', 'version': 1},
           {'product_description': product_description}
       ) AS summarized_product_info
FROM products
GROUP BY category;
```

**Description**: This example uses a pre-configured named prompt (`summarizer`) with version `1` to summarize product descriptions. The results are grouped by category, with one summary per category.

### 1.4. **Advanced Example with Multiple Columns and `GROUP BY`**

Summarize product details by category, using both the product name and description:

```sql
WITH product_info AS (
    SELECT category, product_name, product_description
    FROM products
    WHERE category = 'Electronics'
)
SELECT category,
       llm_reduce(
           {'model_name': 'gpt-4'},
           {'prompt': 'Summarize the following product details'},
           {'product_name': product_name, 'product_description': product_description}
       ) AS detailed_summary
FROM product_info
GROUP BY category;
```

**Description**: In this advanced example, the query summarizes both the `product_name` and `product_description` columns for products in the "Electronics" category, generating a detailed summary for that category.

## 2. **Input Parameters**

### 2.1 **Model Configuration**

- **Parameter**: `model_name` and `secret_name`

#### 2.1.1 Model Selection

- **Description**: Specifies the model used for text generation.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4' }
  ```

#### 2.1.2 Model Selection with Secret

- **Description**: Specifies the model along with the secret name to be used for authentication when accessing the model.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4', 'secret_name': 'your_secret_name' }
  ```

### 2.2. **Prompt Configuration**

Two types of prompts can be used:

1. **Inline Prompt**

   - Directly provides the prompt in the query.
   - **Example**:
     ```sql
     {'prompt': 'Summarize the following product descriptions'}
     ```

2. **Named Prompt**

   - Refers to a pre-configured prompt by name.
   - **Example**:
     ```sql
     {'prompt_name': 'summarizer'}
     ```

3. **Named Prompt with Version**
   - Refers to a specific version of a pre-configured prompt.
   - **Example**:
     ```sql
     {'prompt_name': 'summarizer', 'version': 1}
     ```

### 2.3. **Column Mappings (Optional)**

- **Key**: Column mappings.
- **Purpose**: Maps table columns to prompt variables for input.
- **Example**:
  ```sql
  {'product_name': product_name, 'product_description': product_description}
  ```

## 3. **Output**

- **Type**: Text (string).
- **Behavior**: The function consolidates multiple rows of text into a single output, summarizing or combining the provided data according to the model's response to the prompt.

**Output Example**:  
For a query that aggregates product descriptions, the result could look like:

- **Input Rows**:

  - `product_name`: _"Running Shoes"_
  - `product_name`: _"Wireless Headphones"_
  - `product_name`: _"Smart Watch"_

- **Output**:  
  `"A variety of products including running shoes, wireless headphones, and smart watches, each designed for comfort, convenience, and performance in their respective categories."`
````

## File: docs/docs/aggregate-functions/llm-rerank.md
````markdown
---
title: llm_rerank
sidebar_position: 3
---

# llm_rerank Aggregate Function

The `llm_rerank` aggregate function implements **progressive reranking** using a sliding window strategy, as introduced by Xueguang Ma et al. (2023) in their paper [Zero-Shot Listwise Document Reranking with a Large Language Model](https://arxiv.org/abs/2305.02156). This approach addresses the input length limitations of transformer-based models, which can only process a fixed number of tokens at a time (e.g., `16,384` tokens for `gpt-4o`). When tasked with reranking a list of documents that exceeds the model's token limit, the function uses a sliding window mechanism to progressively rank subsets of documents.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. **Function Overview**

`llm_rerank` is designed to rank a list of documents or rows based on the relevance to a given prompt. When the list length exceeds the model's input limit, the function uses a sliding window strategy to progressively rerank the documents:

### 1.1. **Window Size**

The model ranks a fixed number of documents (e.g., `m` documents) at a time.

### 1.2. **Sliding Window**

After ranking the last `m` documents, the window shifts towards the list's beginning by half its size (`m/2`) and repeats.

### 1.3. **Top-Ranking**

This ensures the most relevant documents reach the top quickly, enhancing the relevance of top results.

While this approach does not fully reorder the entire list, it is effective in improving the top-ranked results by iteratively ranking smaller subsets of documents.

## 2. **Usage Examples**

### 2.1. **Example without `GROUP BY`**

Rerank documents based on their relevance to a given query:

```sql
SELECT llm_rerank(
    {'model_name': 'gpt-4'},
    {'prompt': 'Rank documents by title keywords (AI, emerging tech), content relevance (innovative approaches), recency, and credibility.'},
    {'document_title': document_title, 'document_content': document_content}
) AS reranked_documents
FROM documents;
```

This query will return the documents ordered by relevance based on the provided prompt.

### 2.2. **Example with `GROUP BY`**

Rerank documents for each category based on their relevance:

```sql
SELECT category,
       llm_rerank(
           {'model_name': 'gpt-4'},
           {'prompt': 'Rank documents by title keywords (AI, emerging tech), content relevance (innovative approaches), recency, and credibility.'},
           {'document_title': document_title, 'document_content': document_content}
       ) AS reranked_documents
FROM documents
GROUP BY category;
```

In this case, the query groups documents by category and reranks them within each category based on relevance.

### 2.3. **Using a Named Prompt with `GROUP BY`**

Use a reusable prompt such as "document-ranking" to rank documents based on relevance to a specific query:

```sql
SELECT category,
       llm_rerank(
           {'model_name': 'gpt-4', 'secret_name': 'school_key'},
           {'prompt_name': 'document-ranking', 'version': 1},
           {'document_title': document_title, 'document_content': document_content}
       ) AS reranked_documents
FROM documents
GROUP BY category;
```

### 2.4. **Advanced Example**

Use the `llm_rerank` function to rerank documents based on their content:

```sql
WITH ranked_documents AS (
    SELECT document_title, document_content
    FROM documents
    WHERE category = 'AI'
)
SELECT llm_rerank(
           {'model_name': 'gpt-4'},
           {'prompt': 'Rank documents by title keywords (AI, emerging tech), content relevance (innovative approaches), recency, and credibility.'},
           {'document_title': document_title, 'document_content': document_content}
       ) AS reranked_documents
FROM ranked_documents;
```

This example will rerank the documents within the defined subset.

## 3. **Input Parameters**

### 3.1 **Model Configuration**

- **Parameter**: `model_name` and `secret_name`

#### 3.1.1 Model Selection

- **Description**: Specifies the model used for text generation.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4' }
  ```

#### 3.1.2 Model Selection with Secret

- **Description**: Specifies the model along with the secret name to be used for authentication when accessing the model.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4', 'secret_name': 'your_secret_name' }
  ```

### 3.2. **Prompt Configuration**

Two types of prompts can be used:

1. **Inline Prompt**

   - Directly provides the prompt in the query.
   - **Example**:
     ```sql
     {'prompt': 'Rank documents by title keywords (AI, emerging tech), content relevance (innovative approaches), recency, and credibility.'}
     ```

2. **Named Prompt**

   - Refers to a pre-configured prompt by name.
   - **Example**:
     ```sql
     {'prompt_name': 'document-ranking'}
     ```

3. **Named Prompt with Version**
   - Refers to a specific version of a pre-configured prompt.
   - **Example**:
     ```sql
     {'prompt_name': 'document-ranking', 'version': 1}
     ```

### 3.3. **Column Mappings (Optional)**

- **Key**: Column mappings.
- **Purpose**: Maps table columns to prompt variables for input.
- **Example**:
  ```sql
  {'document_title': document_title, 'document_content': document_content}
  ```

## 4. **Output**

- **Type**: JSON object.
- **Behavior**: The function returns a JSON object containing the reranked documents, ordered by relevance to the prompt. The structure of the returned JSON will mirror the input columns' values.

**Output Example**:  
For a query that reranks documents based on relevance, the result could look like:

- **Input Rows**:

  - `document_title`: _"Introduction to AI"_
  - `document_content`: _"This document covers the basics of artificial intelligence."_

- **Output JSON**:
  ```json
  [
    {
      "document_title": "Introduction to AI",
      "document_content": "This document covers the basics of artificial intelligence."
    },
    {
      "document_title": "Advanced AI Techniques",
      "document_content": "This document explores advanced topics in AI."
    }
  ]
  ```

The output contains the documents ordered by relevance based on the prompt.
````

## File: docs/docs/getting-started/_category_.json
````json
{
  "label": "Getting Started",
  "position": 2,
  "link": {
    "id": "getting-started",
    "type": "doc"
  }
}
````

## File: docs/docs/getting-started/azure.md
````markdown
---
title: Azure
sidebar_position: 1
---

# FlockMTL Using Azure

Before starting, ensure you have followed the [Getting Started](/docs/getting-started) guide to setup FlockMTL. Next you need to get the necesary credentials to use Azure API check the [Microsoft Azure](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference) Page.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## Azure Provider Setup

To use the Azure API, you need only to do two required steps:

- First, create a secret with your Azure API key, resource name, and API version. You can do this by running the following SQL command:

```sql
CREATE SECRET (
    TYPE AZURE_LLM,
    API_KEY 'your-key-here',
    RESOURCE_NAME 'resource-name',
    API_VERSION 'api-version'
);
```

The azure_endpoint will be reconstruct from the _RESOURCE_NAME_ param. If your **azure_endpoint** is `https://my-personal-resource-name.openai.azure.com`, _RESOURCE_NAME_ should be `my-personal-resource-name`.

- Create your Azure model in the model manager. Make sure that the name of the model is unique. You can do this by running the following SQL command:

```sql
CREATE MODEL(
   'QuackingModel',
   'gpt-4o',
   'azure',
   {"context_window": 128000, "max_output_tokens": 16384}
);
```
- Now you simply use FlockMTL with Azure provider. Here's a small query to run to test if everything is working:

```sql
SELECT llm_complete(
    {'model_name': 'QuackingModel'},
    {'prompt': 'Talk like a duck 🦆 and write a poem about a database 📚'}
);
```
````

## File: docs/docs/getting-started/getting-started.md
````markdown
# Getting Started With FlockMTL

FlockMTL as a DuckDB extension is designed to simplify the integration of Large Language Models (LLMs) into your data workflows. This guide will help you get started with FlockMTL, covering installation, setup, and basic usage.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## Install DuckDB

To install Duckdb, it's an easy process you need just to visit [DuckDB Installation Page](https://duckdb.org/docs/installation/) and choose the installation options that represent your environment, by specifying:

- **Version**: Stable or Preview.
- **Environment**: CLI, Python, R, etc.
- **Platform**: Linux, MacOS or Windows.
- **Download Method**: Direct or Package Manager.

After installing DuckDB, you can verify the installation and get started by following the [DuckDB CLI Overview](https://duckdb.org/docs/stable/clients/cli/overview.html/).

## Install FlockMTL Extension

At this stage you should have a running DuckDB instance. To install FlockMTL, run the following SQL commands in your DuckDB instance:

```sql
INSTALL flockmtl FROM community;
LOAD flockmtl;
```

This will install the FlockMTL extension and load it into your DuckDB environment.

## Set Up API Keys for Providers

To use FlockMTL functions, you need to set up API keys for the providers you plan to use. FlockMTL supports multiple providers such as **OpenAI**, **Azure**, and **Ollama**.

Refer to the following sections for detailed instructions on setting up API keys for each provider.

import DocCard from '@site/src/components/global/DocCard';
import { RiOpenaiFill } from "react-icons/ri";
import { VscAzure } from "react-icons/vsc";
import { SiOllama } from "react-icons/si";

<DocCard
  Icon={VscAzure}
  title="Azure"
  link="/flockmtl/docs/getting-started/azure"
   />
<DocCard
  Icon={SiOllama}
  title="Ollama"
  link="/flockmtl/docs/getting-started/ollama"
   />
<DocCard
  Icon={RiOpenaiFill}
  title="OpenAI"
  link="/flockmtl/docs/getting-started/openai"
   />
````

## File: docs/docs/getting-started/ollama.md
````markdown
---
title: Ollama
sidebar_position: 2
---

# FlockMTL Using Ollama

Choosing Ollama is a good option for local model execution. It allows you to run models locally without relying on external APIs. But we should first set up the Ollama API and model. Here's how to do it:

- **Install Ollama**: Ensure Ollama is installed. If not, download it from the [Ollama download page](https://ollama.com/download).
- **Download the Model**: Confirm that the required model is available on your system.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## Ollama Setup

After making sure that you have Ollama installed and the model downloaded, you can start using it with FlockMTL. The same as the other providers only two steps are required:

- First, create a secret with your Ollama API URL. You can do this by running the following SQL command, where Ollama is running locally, and the default URL is `127.0.0.1:11434` :
```sql
CREATE SECRET (
    TYPE OLLAMA,
    API_URL '127.0.0.1:11434'
);
```

- Next, create your Ollama model in the model manager. Make sure that the name of the model is unique, and the model you're using is already downloaded. You can create your model by running the following SQL command:
```sql
CREATE MODEL(
   'QuackingModel',
   'llama3.2',
   'ollama',
   {"context_window": 128000, "max_output_tokens": 2048}
);
```

- Now you simply use FlockMTL with Ollama provider. Here's a small query to run to test if everything is working:
```sql
SELECT llm_complete(
    {'model_name': 'QuackingModel'},
    {'prompt': 'Talk like a duck 🦆 and write a poem about a database 📚'}
);
```
````

## File: docs/docs/getting-started/openai.md
````markdown
---
title: OpenAI  
sidebar_position: 3
---

# FlockMTL Using OpenAI 

In this section we will cover how to set up and use OpenAI provider and OpenAI-Compatible provider with FlockMTL.

Before starting, you should have already followed the [Getting Started](/docs/getting-started) guide.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## OpenAI Provider Setup

To use OpenAI provider, you need first to get your OpenAI API key from the [OpenAI website](https://platform.openai.com/api-keys). Only two steps are required:

- First Creating a secret with your OpenAI API key.
```sql  
CREATE SECRET (
    TYPE OPENAI,
    API_KEY 'your-api-key'
);  
```
- Create your OpenAI model in the model manager. Make sure that the name of the model is unique.
```sql
CREATE MODEL(
   'QuackingModel',
   'gpt-4o', 
   'openai', 
   {"context_window": 128000, "max_output_tokens": 8400}
);
```

- Now you simply use FlockMTL with OpenAI provider. Here's a small query to run to test if everything is working:

```sql
SELECT llm_complete(
        {'model_name': 'QuackingModel'},
        {'prompt': 'Talk like a duck 🦆 and write a poem about a database 📚'}
        );
```

## OpenAI-Compatible Provider Setup

For providers with OpenAI-compatible APIs, specify the `BASE_URL` along with your API key, to illustrate we will use [groq](https://groq.com/) as an example. You need only two required steps:

- First Creating a secret for you `groq` provider by specifying its `BASE_URL` and `API_KEY`.
```sql  
CREATE SECRET (
    TYPE OPENAI,
    BASE_URL 'https://api.groq.com/openai/v1/',
    API_KEY 'your-api-key'
);
```
- Next, create your OpenAI-compatible model in the model manager. Make sure that the name of the model is unique.
```sql
CREATE MODEL(
   'QuackingModel',
   'gpt-4o', 
   'openai', 
   {"context_window": 128000, "max_output_tokens": 8400}
);
```

- Same as before, you can test if everything is working with the same query:

```sql
SELECT llm_complete(
    {'model_name': 'QuackingModel'},
    {'prompt': 'Talk like a duck 🦆 and explain what a database is 📚'}
);
```
````

## File: docs/docs/resource-management/_category_.json
````json
{
  "label": "Resource Management",
  "position": 3,
  "link": {
    "id": "resource-management",
    "type": "doc"
  }
}
````

## File: docs/docs/resource-management/api-keys.md
````markdown
---
title: API Keys
sidebar_position: 3
---

# API Keys Management

FlockMTL uses [DuckDB's Secrets Manager](https://duckdb.org/docs/configuration/secrets_manager.html) to securely store and manage sensitive information like API keys and credentials. Secrets are typed by service provider and can be temporary (in-memory) or persistent (on-disk).

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. Types of Secrets

Supported secret types for FlockMTL:

- **OpenAI**
- **Ollama**
- **Azure**

## 2. Creating a Secret

Secrets can be created with the `CREATE SECRET` SQL command. Temporary secrets are stored in memory, while persistent secrets are stored on disk. If no secret name is provided, DuckDB automatically assigns a default provider name.

### 2.1 OpenAI API Key

```sql
CREATE SECRET (
    TYPE OPENAI,
    API_KEY 'your-api-key'
);
```

This creates a secret named `__default_openai`.

### 2.2 Ollama API URL

```sql
CREATE SECRET (
    TYPE OLLAMA,
    API_URL '127.0.0.1:11434'
);
```

This creates a secret named `__default_ollama`.

### 2.3 Azure API Configuration

```sql
CREATE SECRET (
    TYPE AZURE_LLM,
    API_KEY 'your-key-here',
    RESOURCE_NAME 'resource-name',
    API_VERSION 'api-version'
);
```

This creates a secret named `__default_azure`.

## 3. Persistent Secrets

To persist secrets across DuckDB sessions, use `CREATE PERSISTENT SECRET`:

### 3.1 Example for OpenAI (Persistent):

```sql
CREATE PERSISTENT SECRET (
    TYPE OPENAI,
    API_KEY 'your-api-key'
);
```

### 3.2 Example for Ollama (Persistent):

```sql
CREATE PERSISTENT SECRET (
    TYPE OLLAMA,
    API_URL '127.0.0.1:11434'
);
```

### 3.3 Example for Azure (Persistent):

```sql
CREATE PERSISTENT SECRET (
    TYPE AZURE_LLM,
    API_KEY 'your-key-here',
    RESOURCE_NAME 'resource-name',
    API_VERSION 'api-version'
);
```

## 4. Deleting Secrets

To delete a secret, use the `DROP SECRET` command. For default provider secrets, the name will follow the pattern `__default_<provider_name>`.

### 4.1 Deleting Temporary Secrets

To delete a temporary secret, use:

```sql
DROP TEMPORARY SECRET your_secret_name;
```

For default provider secrets, the name will be in the format `__default_<provider_name>`, e.g., `__default_openai`, `__default_ollama`, or `__default_azure`.

Example for deleting a default temporary OpenAI secret:

```sql
DROP TEMPORARY SECRET __default_openai;
```

### 4.2 Deleting Persistent Secrets

To delete a persistent secret, use:

```sql
DROP PERSISTENT SECRET your_secret_name;
```

For default provider secrets, the name will be in the format `__default_<provider_name>`, e.g., `__default_openai`, `__default_ollama`, or `__default_azure`.

Example for deleting a default persistent OpenAI secret:

```sql
DROP PERSISTENT SECRET __default_openai;
```

## 5. Listing Secrets

To list all secrets:

```sql
FROM duckdb_secrets();
```
````

## File: docs/docs/resource-management/models.md
````markdown
---
title: Models
sidebar_position: 1
---

# Models Management

The **Models Management** section provides guidance on how to manage and configure models for **analytics and semantic analysis tasks** within FlockMTL. These tasks involve processing and analyzing text, embeddings, and other data types using pre-configured models, either system-defined or user-defined, based on specific use cases. Each database is configured with its own model management table during the initial load.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. Model Configuration

Models are stored in a table with the following structure:

| **Column Name**     | **Description**                                                                     |
| ------------------- | ----------------------------------------------------------------------------------- |
| **Model Name**      | Unique identifier for the model                                                     |
| **Model Type**      | Specific model type (e.g., `gpt-4`, `llama3`)                                       |
| **Provider**        | Source of the model (e.g., `openai`, `azure`, `ollama`)                             |
| **Model Arguments** | JSON configuration parameters such as `context_window` size and `max_output_tokens` |

## 2. Management Commands

- Retrieve all available models

```sql
GET MODELS;
```

- Retrieve details of a specific model

```sql
GET MODEL 'model_name';
```

- Create a new user-defined model

```sql
CREATE MODEL('model_name', 'model', 'provider', {'context_window': 128000, 'max_output_tokens': 8000})
```

- Modify an existing user-defined model

```sql
UPDATE MODEL('model_name', 'model', 'provider', {'context_window': 128000, 'max_output_tokens': 8000});
```

- Remove a user-defined model

```sql
DELETE MODEL 'model_name';
```

## 3. SQL Query Examples

### Semantic Text Completion

```sql
SELECT llm_complete(
    {'model_name': 'gpt-4'},
    {'prompt_name': 'product-description'},
    {'input_text': product_description}
) AS generated_description
FROM products;
```

### Semantic Search

```sql
SELECT llm_complete(
    {'model_name': 'semantic_search_model'},
    {'prompt_name': 'search-query'},
    {'search_query': query}
) AS search_results
FROM search_data;
```

## 4. Global and Local Models

Model creation is database specific if you want it to be available irrespective of the database then make it a GLOBAL mode. Note that previously, the creation was specific to the running database, which is LOCAL by default and the keyword LOCAL is optional.

### Create Models

- Create a global model:

```sql
CREATE GLOBAL MODEL('model_name', 'model_type', 'provider', {'context_window': 128000, 'max_output_tokens': 8000})
```

- Create a local model (default if no type is specified):

```sql
CREATE LOCAL MODEL('model_name', 'model_type', 'provider', {'context_window': 128000, 'max_output_tokens': 8000})
CREATE MODEL('model_name', 'model_type', 'provider', {'context_window': 128000, 'max_output_tokens': 8000})
```

### Toggle Model State

- Toggle a model's state between global and local:

```sql
UPDATE MODEL 'model_name' TO GLOBAL;
UPDATE MODEL 'model_name' TO LOCAL;
```

All the other queries remain the same for both global and local prompts.
````

## File: docs/docs/resource-management/prompts.md
````markdown
---
title: Prompts
sidebar_position: 2
---

# Prompts Management

The **Prompt Management** section provides guidance on how to manage and configure prompts for **analytics and semantic analysis tasks** within FlockMTL. Prompts guide models in generating specific outputs for tasks like content generation, summarization, and ranking. Each database is configured with its own prompt management table during the initial load.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

### 1. Prompt Table Structure

| **Column Name** | **Description**                   |
| --------------- | --------------------------------- |
| **prompt_name** | Unique identifier for the prompt  |
| **prompt**      | Instruction content for the model |
| **updated_at**  | Timestamp of the last update      |
| **version**     | Version number of the prompt      |

## 2. Management Commands

- Retrieve all available prompts

```sql
GET PROMPTS;
```

- Retrieve details of a specific prompt

```sql
GET PROMPT 'prompt_name';
```

- Create a new prompt

```sql
CREATE PROMPT('prompt_name', 'prompt');
```

- Modify an existing prompt

```sql
UPDATE PROMPT('prompt_name', 'prompt');
```

- Remove a prompt

```sql
DELETE PROMPT 'prompt_name';
```

## 3. SQL Query Examples

### Semantic Text Completion

Generate a description for products using a predefined prompt:

```sql
SELECT llm_complete(
    {'model_name': 'gpt-4'},
    {'prompt_name': 'product-description'},
    {'input_text': product_description}
) AS generated_description
FROM products;
```

### Review Summary

Generate a summary for customer reviews using a specific prompt version:

```sql
SELECT llm_complete(
    {'model_name': 'semantic_search_model'},
    {'prompt_name': 'customer-review-summary', 'version': 3},
    {'customer_review': review_text}
) AS review_summary
FROM reviews;
```

## 4. Global and Local Prompts

Prompt creation is database specific if you want it to be available irrespective of the database then make it a GLOBAL mode. Note that previously, the creation was specific to the running database, which is LOCAL by default and the keyword LOCAL is optional.

### Create Prompts

*   Create a global prompt:

```sql
CREATE GLOBAL PROMPT('prompt_name', 'prompt');
```

- Create a local prompt (default if no type is specified):

```sql
CREATE LOCAL PROMPT('prompt_name', 'prompt');
CREATE PROMPT('prompt_name', 'prompt');
```

### Toggle Prompt State

- Toggle a prompt's state between global and local:

```sql
UPDATE PROMPT 'prompt_name' TO GLOBAL;
UPDATE PROMPT 'prompt_name' TO LOCAL;
```

All the other queries remain the same for both global and local prompts.
````

## File: docs/docs/resource-management/resource-management.md
````markdown
# Resource Management in FlockMTL

Resource Management is a critical component of FlockMTL that provides comprehensive tools for managing models, prompts, and secrets essential to semantic analytics tasks.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. Models

[Model Management](/docs/resource-management/models) allows configuration of both system-defined and user-defined models for various semantic analytics purposes.

### Key Capabilities:

1. **System-Defined Models**: Pre-configured for common tasks like text summarization and embedding generation.
2. **User-Defined Models**: Customizable models with flexible parameter configuration.
3. **Easy Management**: View, create, update, and delete models as needed.

## 2. Prompts

[Prompt Management](/docs/resource-management/prompts) enables precise control over how models interact with data by defining structured guidance for model outputs.

### Key Features:

1. **Custom Prompt Creation**: For specific business tasks.
2. **Version Control**: For prompt evolution.
3. **Update or Remove Prompts**: As requirements change.

## 3. Secrets

[Secrets Management](/docs/resource-management/api-keys) provides secure storage and handling of sensitive authentication credentials for external model providers.

### Key Attributes:

1. **Secure Storage**: Of API keys for providers like OpenAI and Azure.
2. **Centralized Management**: Of third-party service credentials.
3. **Create, Update, and Delete Secrets**: Efficiently.

## 4. Benefits of Resource Management

Effective resource management in FlockMTL delivers:

1. **Customization of Models**: For specific tasks.
2. **Enhanced Security**: For external integrations.
3. **Improved Workflow Efficiency**.
4. **Scalable Semantic Analytics Capabilities**.

By offering intuitive control over models, prompts, and secrets, FlockMTL enables users to focus on using advanced analytics without getting entangled in complex configurations.
````

## File: docs/docs/scalar-functions/_category_.json
````json
{
  "label": "Scalar Functions",
  "position": 4,
  "link": {
    "id": "scalar-functions",
    "type": "doc"
  }
}
````

## File: docs/docs/scalar-functions/llm-complete-json.md
````markdown
---
title: llm_complete_json
sidebar_position: 2
---

# llm_complete_json Function

The `llm_complete_json` function extends the capabilities of `llm_complete` by producing JSON responses.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. Simple Usage (without data)

### 1.1 Using an Inline Prompt

```sql
WITH product_data AS (
    SELECT 
        product_id, 
        product_name, 
        llm_complete_json(
            {'model_name': 'gpt-4'}, 
            {'prompt': 'Using the next product name generate detailed product information that contains name, description and a list of features.'},
            {'product_name': product_name}
        ) AS product_info
    FROM products
)
SELECT 
    product_id, 
    product_info.name AS name, 
    product_info.description AS description
FROM product_data;
```

**Description**: This example uses an inline prompt to generate detailed product information in JSON format. The `gpt-4` model is used to process the `product_name` column and generate structured data such as `name`, `description`, and `features` for each product.

### 1.2 Using a Named Prompt

```sql
WITH product_features AS (
    SELECT 
        product_id, 
        llm_complete_json(
            {'model_name': 'reduce-model', 'secret_name': 'my_new_key'}, 
            {'prompt_name': 'product-features', 'version': 1}, 
            {'product_name': product_name}
        ) AS feature_info
    FROM products
)
SELECT 
    product_id, 
    feature_info.name AS name, 
    feature_info.features AS features
FROM product_features;
```

**Description**: This example demonstrates the use of a named prompt (`product-features`) with version `1` to generate structured JSON data. The `reduce-model` processes the `product_name` column and outputs the product name along with a list of its features.

## 2. Actual Usage (with data)

```sql
WITH detailed_products AS (
    SELECT 
        product_id, 
        llm_complete_json(
            {'model_name': 'gpt-4'}, 
            {'prompt': 'Using the next product name generate detailed product information that contains name, description and a list of features.'}, 
            {'product_name': product_name}
        ) AS product_summary
    FROM products
)
SELECT 
    product_id, 
    product_summary.name AS name, 
    product_summary.description AS description,
    json_array_length(product_summary.features) AS feature_count
FROM detailed_products
WHERE json_array_length(product_summary.features) > 2;
```

**Description**: This actual example uses the `gpt-4` model to generate detailed product information, including a list of features. The query also calculates the number of features (`feature_count`) using `json_array_length()` and filters out products with fewer than 3 features.

## 3. Input Parameters

The `llm_complete` function accepts three structured inputs: model configuration, prompt configuration, and input data columns.

### 3.1 Model Configuration

- **Parameter**: `model_name` and `secret_name`

#### 3.1.1 Model Selection

- **Description**: Specifies the model used for text generation.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4' }
  ```

#### 3.1.2 Model Selection with Secret

- **Description**: Specifies the model along with the secret name to be used for authentication when accessing the model.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4', 'secret_name': 'your_secret_name' }
  ```

### 3.2 Prompt Configuration

- **Parameter**: `prompt` or `prompt_name`

  #### 3.2.1 Inline Prompt

  Directly provides the prompt.

  - **Example**:
    ```sql
    { 'prompt': 'Summarize the content of the article.' }
    ```

  #### 3.2.2 Named Prompt

  References a pre-configured prompt.

  - **Example**:
    ```json
    { 'prompt_name': 'summarize-content' }
    ```

  #### 3.2.3 Named Prompt with Version

  References a specific version of a prompt.

  - **Example**:
    ```json
    { 'prompt_name': 'summarize-content', 'version': 2 }
    ```

### 3.3 Input Data Columns (OPTIONAL)

- **Parameter**: Column mappings
- **Description**: Specifies the columns from the table to be passed to the model as input.
- **Example**:
  ```sql
  {'product_name': product_name, 'product_description': product_description}
  ```

## 4. Output

The function returns a **JSON object** for each row, which can be accessed dynamically to retrieve specific fields.

**Example Output**:  
For a prompt like *"Generate detailed product information that contains name, description and a list of features."*, you might see:  
- **Input Row**:  
  - `product_name`: *"Wireless Headphones"*  
- **Output JSON**:  
  ```json
  {
    "name": "Wireless Headphones",
    "description": "High-quality headphones with noise cancellation.",
    "features": ["Wireless", "Noise Cancellation", "Extended Battery Life"]
  }
  ```

You can access individual fields such as `.name`, `.description`, or `.features` for downstream tasks.
````

## File: docs/docs/scalar-functions/llm-complete.md
````markdown
---
title: llm_complete
sidebar_position: 1
---

# llm_complete Function

The `llm_complete` function generates text completions using specified models and prompts for dynamic data generation.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. Simple Usage (without data)

### 1.1 Inline Prompt

```sql
SELECT llm_complete(
    {'model_name': 'gpt-4'},
    {'prompt': 'Explain the purpose of FlockMTL.'}
) AS flockmtl_purpose;
```

**Description**: This example uses an inline prompt to generate a text completion with the `gpt-4` model. The prompt asks the model to explain the purpose of FlockMTL. The function returns a completion for each row based on the provided prompt.

### 1.2 Named Prompt

```sql
SELECT llm_complete(
    {'model_name': 'summarizer', 'secret_name': 'summarizer_secret'},
    {'prompt_name': 'description-generation', 'version': 1},
    {'product_name': product_name}
) AS product_description
FROM products;
```

**Description**: In this example, a named prompt `description-generation` is used with the `summarizer` model. The function generates product descriptions using data from the `product_name` column for each row in the `products` table.

## 2. Actual Usage (with data)

```sql
WITH enhanced_products AS (
    SELECT
        product_id,
        product_name,
        llm_complete(
            {'model_name': 'reduce-model'},
            {'prompt_name': 'summarize-content', 'version': 2},
            {'product_name': product_name}
        ) AS enhanced_description
    FROM products
)
SELECT product_id, product_name, enhanced_description
FROM enhanced_products
WHERE LENGTH(enhanced_description) > 50;
```

**Description**: This actual example demonstrates the use of a pre-configured prompt `summarize-content` with version `2` and the `reduce-model`. It processes the `product_name` column and generates a summarized description. The query then filters out rows where the generated description is shorter than 50 characters.

## 3. Input Parameters

The `llm_complete` function accepts three structured inputs: model configuration, prompt configuration, and input data columns.

### 3.1 Model Configuration

- **Parameter**: `model_name` and `secret_name`

#### 3.1.1 Model Selection

- **Description**: Specifies the model used for text generation.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4' }
  ```

#### 3.1.2 Model Selection with Secret

- **Description**: Specifies the model along with the secret name to be used for authentication when accessing the model.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4', 'secret_name': 'your_secret_name' }
  ```

### 3.2 Prompt Configuration

- **Parameter**: `prompt` or `prompt_name`

  #### 3.2.1 Inline Prompt

  Directly provides the prompt.

  - **Example**:
    ```sql
    { 'prompt': 'Summarize the content of the article.' }
    ```

  #### 3.2.2 Named Prompt

  References a pre-configured prompt.

  - **Example**:
    ```json
    { 'prompt_name': 'summarize-content' }
    ```

  #### 3.2.3 Named Prompt with Version

  References a specific version of a prompt.

  - **Example**:
    ```json
    { 'prompt_name': 'summarize-content', 'version': 2 }
    ```

### 3.3 Input Data Columns (OPTIONAL)

- **Parameter**: Column mappings
- **Description**: Specifies the columns from the table to be passed to the model as input.
- **Example**:
  ```sql
  {'product_name': product_name, 'product_description': product_description}
  ```

## 4. Output

The function generates a text completion for each row based on the provided prompt and input data.

- **Type**: Text (string)
- **Behavior**: Maps over each row and generates a response per tuple.
````

## File: docs/docs/scalar-functions/llm-embedding.md
````markdown
---
title: llm_embedding
sidebar_position: 4
---

# llm_embedding Function

The `llm_embedding` function generates vector embeddings that represent the semantic meaning of text from specified table columns.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. Simple Usage (without data)

### 1.1 Basic Embedding Generation

```sql
SELECT llm_embedding(
    {'model_name': 'text-embedding-3-small', 'secret_name': 'embedding_secret'}, 
    {'product_name': product_name, 'product_description': product_description}
) AS product_embedding
FROM products;
```

**Description**: This example generates vector embeddings for each product, combining the `product_name` and `product_description` columns using the `text-embedding-3-small` model. The output is a semantic vector that represents the content of the product's name and description.

### 1.2 Similarity Search

```sql
WITH product_embeddings AS (
    SELECT 
        product_id, 
        product_name, 
        llm_embedding(
            {'model_name': 'text-embedding-3-small'}, 
            {'product_name': product_name, 'product_description': product_description}
        ) AS product_embedding
    FROM products
)
SELECT 
    a.product_name, 
    b.product_name, 
    array_cosine_similarity(a.product_embedding::DOUBLE[1536], b.product_embedding::DOUBLE[1536]) AS similarity
FROM product_embeddings a
JOIN product_embeddings b
ON a.product_id != b.product_id
WHERE similarity > 0.8;
```

**Description**: This example demonstrates how to use the vector embeddings for similarity search. It calculates the cosine similarity between embeddings of different products to find similar items based on their semantic meaning. Only product pairs with a similarity greater than `0.8` are included.

## 2. Input Parameters

The `llm_embedding` function accepts two primary inputs: model configuration and column mappings.

### 2.1 Model Configuration

- **Parameter**: `model_name` and `secret_name`

#### 2.1.1 Model Selection

- **Description**: Specifies the model used for text generation.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4' }
  ```

#### 2.1.2 Model Selection with Secret

- **Description**: Specifies the model along with the secret name to be used for authentication when accessing the model.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4', 'secret_name': 'your_secret_name' }
  ```

### 2.2 Column Mappings

- **Parameter**: Column mappings
- **Description**: Specifies the columns from the table to be passed to the model for embedding generation.
- **Example**:
  ```sql
  { 'product_name': product_name, 'product_description': product_description }
  ```

## 3. Output

The function returns a **JSON array** containing floating-point numbers that represent the semantic vector of the input text.

**Example Output**:  
For a product with the description *"Wireless headphones with noise cancellation"*, the output might look like this:

```json
[0.342, -0.564, 0.123, ..., 0.789]
```

This array of floating-point numbers encodes the semantic meaning of the product description in high-dimensional space.
````

## File: docs/docs/scalar-functions/llm-filter.md
````markdown
---
title: llm_filter
sidebar_position: 3
---

# llm_filter Function

The `llm_filter` function evaluates a condition based on a given prompt and returns a boolean value (`TRUE` or `FALSE`). This function mostly used in the workload of `WHERE` clause of a query.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. Simple Usage (without data)

### 1.1 Using an Inline Prompt

```sql
SELECT * 
FROM products
WHERE llm_filter(
    {'model_name': 'gpt-4'}, 
    {'prompt': 'Is this product description eco-friendly?'}, 
    {'description': product_description}
);
```

**Description**: This example uses an inline prompt to filter rows based on whether the product description is considered eco-friendly by the `gpt-4` model. If the model returns `TRUE`, the row is included in the result.

### 1.2 Using a Named Prompt

```sql
SELECT * 
FROM products
WHERE llm_filter(
    {'model_name': 'gpt-4'}, 
    {'prompt_name': 'eco-friendly-check'}, 
    {'description': product_description}
);
```

**Description**: In this example, a named prompt (`eco-friendly-check`) is used to determine if the product description is eco-friendly. This allows for reusing pre-configured prompts for similar filtering tasks.

### 1.3 Combining with Other SQL Logic

```sql
WITH filtered_products AS (
    SELECT product_id, product_name, product_description
    FROM products
    WHERE llm_filter(
        {'model_name': 'gpt-4', 'secret_name': 'openai_key'}, 
        {'prompt': 'Is this product description eco-friendly?'}, 
        {'description': product_description}
    )
)
SELECT * FROM filtered_products;
```

**Description**: This example demonstrates how to combine `llm_filter` with other SQL logic. It filters the products based on the eco-friendliness of their descriptions and processes the result in a subquery for further use.

### 1.4 Actual Usage (with data)

```sql
WITH relevant_reviews AS (
    SELECT review_id, review_content
    FROM reviews
    WHERE llm_filter(
        {'model_name': 'gpt-4'}, 
        {'prompt': 'Does this review content contain a positive sentiment?'}, 
        {'content': review_content}
    )
)
SELECT * FROM relevant_reviews
WHERE LENGTH(review_content) > 50;
```

**Description**: This actual example uses `llm_filter` to filter reviews based on positive sentiment. It then further filters the results to only include reviews with content longer than 50 characters.

## 2. Input Parameters

The `llm_filter` function accepts three structured inputs: model configuration, prompt configuration, and input data columns.

### 2.1 Model Configuration

- **Parameter**: `model_name` and `secret_name`

#### 2.1.1 Model Selection

- **Description**: Specifies the model used for text generation.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4' }
  ```

#### 2.1.2 Model Selection with Secret

- **Description**: Specifies the model along with the secret name to be used for authentication when accessing the model.
- **Example**:
  ```sql
  { 'model_name': 'gpt-4', 'secret_name': 'your_secret_name' }
  ```

### 2.2 Prompt Configuration

- **Parameter**: `prompt` or `prompt_name`

  #### 2.2.1 Inline Prompt

  Directly provides the prompt.

  - **Example**:
    ```sql
    { 'prompt': 'Summarize the content of the article.' }
    ```

  #### 2.2.2 Named Prompt

  References a pre-configured prompt.

  - **Example**:
    ```json
    { 'prompt_name': 'summarize-content' }
    ```

  #### 2.2.3 Named Prompt with Version

  References a specific version of a prompt.

  - **Example**:
    ```json
    { 'prompt_name': 'summarize-content', 'version': 2 }
    ```

### 2.3 Input Data Columns (OPTIONAL)

- **Parameter**: Column mappings
- **Description**: Specifies the columns from the table to be passed to the model as input.
- **Example**:
  ```sql
  {'product_name': product_name, 'product_description': product_description}
  ```

## 3. Output

The function returns a **BOOLEAN** value (`TRUE` or `FALSE`), indicating whether the row satisfies the condition specified in the prompt.

**Example Output**:  
For a prompt like *"Is this product description eco-friendly?"*:

- **Input Row**:  
  - `product_description`: *"Made from 100% recyclable materials, this product is perfect for eco-conscious buyers."*
- **Output**:  
  - `TRUE`
````

## File: docs/docs/scalar-functions/scalar-functions.md
````markdown
# Scalar Functions Overview

Scalar functions in FlockMTL operate on data row-by-row, providing powerful operations for text processing, embeddings, and machine learning tasks directly within SQL queries.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## 1. Available Functions

- [`llm_complete`](/docs/scalar-functions/llm-complete): Generates text completions based on model and prompt

- [`llm_complete_json`](/docs/scalar-functions/llm-complete-json): Generates text completions in JSON format for structured output

- [`llm_filter`](/docs/scalar-functions/llm-filter): Filters rows based on a prompt and returns boolean values

- [`llm_embedding`](/docs/scalar-functions/llm-embedding): Generates vector embeddings for text data, used for similarity search and machine learning tasks

## 2. Function Characteristics

- Applied row-by-row to table data
- Supports text generation, filtering, and embeddings

## 3. Use Cases

- Text generation
- Dynamic filtering
- Semantic text representation
- Machine learning feature creation
````

## File: docs/docs/faq.mdx
````
---
title: Frequently Asked Questions (FAQ)
sidebar_position: 7
---

import Collapse from '@site/src/components/global/Collapse';

# Frequently Asked Questions (FAQ)

This section addresses common questions related to FlockMTL, including its features, usage, and best practices. If your question is not answered here, feel free to [contact us](mailto:amine.mhedhbi@polymtl.ca,anasdorbani@gmail.com) or refer to other sections in the documentation.

---

## General Questions

<Collapse title="What is FlockMTL?">
FlockMTL is an extension for DuckDB designed to bring  semantic analysis capabilities directly into your SQL queries. It deeply integrates capabilities of language models and retrieval-augmented generation using a set of map and reduce functions.
</Collapse>

<Collapse title="Who can benefit from using FlockMTL?">
FlockMTL is designed for developers, data scientists, and businesses that need to leverage semantic analysis alongside traditional SQL operations. It’s especially valuable for use cases like document ranking, content generation, and semantic search.
</Collapse>

---

## Features

<Collapse title="What are the key features of FlockMTL?">
FlockMTL offers:
- **Model Management**: Configure system-defined and user-defined models.
- **Prompt Management**: Create and manage reusable text prompts.
- **API Keys Management**: Store and manage API keys securely for supported providers.
- **Integration with DuckDB**: Leverage DuckDB’s powerful SQL engine alongside semantic capabilities.
- **Support for Multiple Providers**: Access OpenAI, Azure, and Ollama models for various tasks.
- **Local Inference with Ollama**: Perform inference on-premises with LLaMA models.
- **Scalar Functions**: Use functions like `llm_complete`, `llm_complete_json`, and `llm_filter` for advanced tasks.
- **Aggregate Functions**: Perform summarization, ranking, and reordering with functions like `llm_reduce` and `llm_rerank`.
</Collapse>

<Collapse title="Which providers are supported in FlockMTL?">
FlockMTL currently supports:
- **OpenAI**
- **Azure**
- **Ollama**
</Collapse>

---

## Installation and Setup

<Collapse title="How do I install FlockMTL?">
You can install FlockMTL sinmply by running the following command:
```sql
INSTALL flockmtl FROM community;
LOAD flockmtl;
```
</Collapse>

<Collapse title="Are there any prerequisites for using FlockMTL?">
Yes, you need:
- DuckDB (latest version recommended).
- API keys for the providers you plan to use (e.g., OpenAI, Azure).
- For local inference with Ollama, ensure the appropriate hardware and dependencies are installed.
</Collapse>

---

## Using FlockMTL

<Collapse title="How do I manage models in FlockMTL?">
You can manage models using SQL commands like:
- `CREATE MODEL`
- `UPDATE MODEL`
- `DELETE MODEL`
Refer to the [Model Management](/docs/resource-management/models) section for detailed examples.
</Collapse>

<Collapse title="How do I set up secrets for providers?">
Check the [Secrets Management](/docs/resource-management/api-keys) section for a step-by-step guide.
</Collapse>

<Collapse title="Can I create custom prompts for my tasks?">
Yes, you can create and manage custom prompts using the `CREATE PROMPT` and `UPDATE PROMPT` commands. See the [Prompt Management](/docs/resource-management/prompts) section for more details.
</Collapse>

---

## Troubleshooting

<Collapse title="What should I do if a query fails?">
- Verify that the model and provider are correctly configured.
- Ensure the secret keys for providers are valid and up-to-date.
- Check the input data for any inconsistencies.
</Collapse>

<Collapse title="How do I debug API-related errors?">
- Check your API usage limits and ensure the key is active.
- Use the `GET SECRET` command to confirm the correct key is being used.
- Look at error messages from the provider (e.g., OpenAI or Azure).
</Collapse>

<Collapse title="Why is the response time slow for some queries?">
Response times may vary based on:
- The provider (e.g., API latency for OpenAI or Azure).
- The complexity of the query.
- Hardware limitations (for local inference with Ollama).
- The batch size used during inference.
- The model's context window:
  - Larger context windows may increase processing time.
  - Smaller context windows with large datasets can lead to multiple API calls, increasing latency.
</Collapse>

---

## Additional Help

<Collapse title="Where can I find more resources on FlockMTL?">
- [Official Documentation](/docs/what-is-flockmtl)
- [GitHub Repository](https://github.com/dsg-polymtl/flockmtl-duckdb)
- [Main Website](/)
</Collapse>

<Collapse title="How can I contact support?">
For technical support, [email us](mailto:amine.mhedhbi@polymtl.ca,anasdorbani@gmail.com).
</Collapse>

---

Got more questions? [Let us know](mailto:amine.mhedhbi@polymtl.ca,anasdorbani@gmail.com), and we’ll be happy to assist!
````

## File: docs/docs/hybrid-search.md
````markdown
---
title: Hybrid Search
sidebar_position: 6
---

# Hybrid Search using FlockMTL
## Overview
FlockMTL provides a set of fusion functions that allow you to combine multiple scoring systems into a single, unified relevance score. This is particularly useful in hybrid search scenarios where you want to leverage the strengths of different scoring methods (e.g., BM25 and vector similarity scores) to produce the best-fit result. To achieve that, FlockMTL offers two types of fusion functions: rank-based and score-based.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## Rank-Based Fusion Algorithm
The input to the rank-based fusion algorithm is each document's ranking in n scoring systems, from best to worst, where 1 is the best-ranked document. Multiple documents can have the same rank and will be treated as equal.
### `fusion_rrf`
Performs Reciprocal Rank Fusion (RRF). Each document's combined score is calculated using the following formula:
$$
combined\_score = \sum_{n=1}^{N} \frac{1}{60 + \text{ranking}_n}
$$
where `N` represents the number of scoring systems and `ranking_n` represents the rank of the document in that scoring system.

Performs Reciprocal Rank Fusion (RRF) as described by [Cormack et al](https://doi.org/10.1145/1571941.1572114).

* Gordon V. Cormack, Charles L A Clarke, and Stefan Buettcher. 2009. Reciprocal rank fusion outperforms condorcet and individual rank learning methods. In Proceedings of the 32nd international ACM SIGIR conference on Research and development in information retrieval (SIGIR '09). Association for Computing Machinery, New York, NY, USA, 758–759. https://doi.org/10.1145/1571941.1572114

## Score-Based Fusion Algorithms
The input to the score-based fusion algorithms is n normalized sets of scores. The scores must be normalized because different scoring systems often use different scales for their scores. To ensure that all scoring systems are treated equally, they must first be normalized.
### `fusion_combsum`
Sums over all normalized scores for each document. Please note that NULL, NaN, and 0 values are all treated as 0.

### `fusion_combmnz`
Sums over all normalized scores for each document and multiplies that sum by the number of scoring systems which found the document (hit count). A hit constitutes any score greater than 0. Please note that NULL, NaN, and 0 values are all treated as 0. Each document's combined score is calculated using the following formula:
$$
combined\_score = hit\_count * \sum_{n=1}^{N} normalized\_score_n
$$
where $N$ represents the number of scoring systems, $normalized\_score_n$ represents the normalized score of the document in that scoring system, and $hit\_count$ represents the number of non-zero scores that the document has.

### `fusion_combmed`
Takes the median of all scores for each document. Please note that NULL, NaN, and 0 values are all treated as 0 and are considered when calculating the median. If the inputs are `(NULL, NULL, 1.0)`, then the median returned is 0.

### `fusion_combanz`
Calculates the average normalized score for each document. Please note that NULL, NaN, and 0 values are all treated as 0 and are considered when calculating the average. If the inputs are `(NULL, NULL, 1.0)`, then the average returned is $0.\overline{3}$.

A variety of algorithms as described by [fox et al](https://trec.nist.gov/pubs/trec2/papers/txt/23.txt).

## Data pre-processing
### Rank-Based Algorithm
The input to the rank-based algorithm is 1 or more sets of rankings for each document. This ranking can be obtained by using the DENSE_RANK() function, as shown in the following sample query:
```sql
SELECT 
    index_column,
    bm25_score,
    DENSE_RANK() OVER (ORDER BY bm25_score DESC) AS bm25_rank
FROM bm25_scores;
```

### Score-Based Algorithm
The input to score-based algorithms are 1 or more sets of normalized scores for each document. These normalized scores can be obtained directly in SQL. Note that division by 0 (eg. when min = max) results in NaN values. As mentioned above, these are treated by the fusion algorithms as 0. The following sample query performs min-max normalization:
```sql
WITH min_max AS (
    SELECT
        MIN(bm25_score) AS min,
        MAX(bm25_score) AS max
    FROM bm25_scores
)
SELECT 
    index_column,
    bm25_score,
    (bm25_score - min) / (max - min) AS normalized_bm25
FROM bm25_scores, min_max;
```

## 1. Basic Usage Examples
All score-based fusion algorithms use the same syntax. In the following examples, fusion_combsum can be replaced by any of the score-based fusion algorithms presented above.

### 1.1 Simple Example: Combining Two Scores
### Rank-Based Algorithm

```sql
SELECT fusion_rrf(1, 1);
```

**Description**: In this simple example, the `fusion_rrf` function takes two ranks (1 and 1) as inputs and returns the combined score.

**Output**:

```sql
0.03278688524590164
```

### Score-Based Algorithms
```sql
SELECT fusion_combsum(0.4, 0.5);
```

**Output**:

```sql
0.9
```

### 1.2 Example with BM25 and Embedding Scores
### Rank-Based Algorithm

```sql
SELECT
    fusion_rrf(bm25_rank, embedding_rank) AS combined_score
FROM search_results;
```

**Description**: This query combines the BM25 rank (`bm25_rank`) and the embedding rank (`embedding_rank`) for each row in the `search_results` table. The function merges both scores into a single `combined_score`.

### Score-Based Algorithms
```sql
SELECT
    fusion_combsum(bm25_normalized, embedding_normalized) AS combined_score
FROM search_results;
```

**Description**: This query combines the normalized BM25 score (`bm25_normalized`) and the normalized embedding score (`embedding_normalized`) for each row in the `search_results` table. The function merges both scores into a single `combined_score`.

## 2. Advanced Example

```sql
WITH combined_scores AS (
    SELECT
        index_column,
        fusion_combsum(bm25_normalized, embedding_normalized) AS combined_score
    FROM search_results
)
SELECT
    index_column,
    combined_score
FROM combined_scores
ORDER BY combined_score DESC;
```

**Description**: In this example, the query merges BM25 and embedding scores into a `combined_score` for each document and sorts the results by `combined_score` in descending order, prioritizing more relevant documents. The same can be done with `fusion_rrf`

## 3. Input Parameters

The fusion functions (score-based and rank-based) accept **two or more numerical inputs**. While examples below show two inputs for simplicity, the functions are designed to handle any number of inputs.

### 3.1 Numerical Inputs

- **Parameter**: One or more numeric values (e.g., normalized scores from different systems)
- **Description**: Each input represents a score from a distinct retrieval method (e.g., BM25, vector similarity search, etc.). These values are combined by the fusion algorithm.
- **Example**: `0.4, 0.9, 0.7`

> 💡 You can pass any number of numerical inputs—two or more—depending on how many scoring systems you’re combining.
````

## File: docs/docs/what-is-flockmtl.md
````markdown
---
sidebar_position: 1
---

# What is FlockMTL?

## Overview

**FlockMTL** enhances DuckDB by integrating semantic functions and robust resource management capabilities, enabling advanced analytics and language model operations directly within SQL queries.

import TOCInline from '@theme/TOCInline';

<TOCInline toc={toc} />

## Semantic Functions

FlockMTL offers a suite of semantic functions that allow users to perform various language model operations:

- **Scalar Map Functions**:
    - [`llm_complete`](/docs/scalar-functions/llm-complete): Generates text completions using a specified language model.
    - [`llm_complete_json`](/docs/scalar-functions/llm-complete-json): Produces JSON-formatted text completions.
    - [`llm_filter`](/docs/scalar-functions/llm-filter): Filters data based on language model evaluations, returning boolean values.
    - [`llm_embedding`](/docs/scalar-functions/llm-embedding): Generates embeddings for input text, useful for semantic similarity tasks.

- **Aggregate Reduce Functions**:
    - [`llm_reduce`](/docs/aggregate-functions/llm-reduce): Aggregates multiple inputs into a single output using a language model.
    - [`llm_reduce_json`](/docs/aggregate-functions/llm-reduce-json): Similar to `llm_reduce`, but outputs JSON-formatted results.
    - [`llm_rerank`](/docs/aggregate-functions/llm-rerank): Reorders query results based on relevance scores from a language model.
    - [`llm_first`](/docs/aggregate-functions/llm-first): Selects the top-ranked result after reranking.
    - [`llm_last`](/docs/aggregate-functions/llm-last): Selects the bottom-ranked result after reranking.


This allows users to perform tasks such as text generation, summarization, classification, filtering, fusion, and embedding generation.

## Hybrid Search Functions

FlockMTL also provides functions that support hybrid search. Namely, the following data fusion algorithms to combine scores of various retrievers:

- [**`fusion_rrf`**](/docs/hybrid-search#fusion_rrf): Implements Reciprocal Rank Fusion (RRF) to combine rankings from multiple scoring systems.
- [**`fusion_combsum`**](/docs/hybrid-search#fusion_combsum): Sums normalized scores from different scoring systems.
- [**`fusion_combmnz`**](/docs/hybrid-search#fusion_combmnz): Sums normalized scores and multiplies by the hit count.
- [**`fusion_combmed`**](/docs/hybrid-search#fusion_combmed): Computes the median of normalized scores.
- [**`fusion_combanz`**](/docs/hybrid-search#fusion_combanz): Calculates the average of normalized scores.

These functions enable users to combine the strengths of different scoring methods, such as BM25 and embedding scores, to produce the best-fit results, and even create end-to-end RAG pipelines.

We believe that relational DBMSs and LLMs are a match made in heaven. We are leaning on the tradition of declarative interfaces to unburden users from lower-level implementation details. Users can query both structured and unstructred datasets while combining analytics and semantic analysis directly within SQL.

## Resource Management

FlockMTL introduces a [**resource management**](/docs/resource-management) framework that treats models (`MODEL`) and prompts (`PROMPT`) similarly to tables, allowing for organized storage and retrieval.

## System Requirements

FlockMTL is supported by the different operating systems and platforms, such as:
- Linux
- macOS
- Windows

And to ensure stable and reliable performance, it is important to meet only two requirements:
- **DuckDB Setup**: Version 1.1.1 or later. FlockMTL is compatible with the latest stable release of DuckDB, which can be installed from the official [DuckDB installation guide](https://duckdb.org/docs/installation/index?version=stable&environment=cli&platform=linux&download_method=direct&architecture=x86_64).
- **Provider API Key**: FlockMTL supports multiple providers such as **OpenAI**, **Azure**, and **Ollama**. Configure the provider of your choice to get started.
````

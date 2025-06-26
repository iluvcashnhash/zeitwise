# Meme Generation API

This document describes the API endpoints for generating and managing memes in the ZeitWise application.

## Base URL

All endpoints are prefixed with `/api/memes`.

## Authentication

All endpoints require authentication using a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### 1. Generate a Meme

Start an asynchronous task to generate a meme based on the provided headline, analysis, and style.

```http
POST /generate
```

**Request Body:**
```json
{
  "headline": "AI takes over the world",
  "analysis": "Analysis shows AI development is accelerating",
  "style": "funny"
}
```

**Response:**
- `202 Accepted`: Meme generation started
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication token
- `500 Internal Server Error`: Failed to start generation

**Example Response:**
```json
{
  "status": "pending",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Meme generation started",
  "data": {
    "headline": "AI takes over the world",
    "style": "funny"
  }
}
```

### 2. Check Meme Generation Status

Check the status of a meme generation task.

```http
GET /status/{task_id}
```

**Path Parameters:**
- `task_id` (required): The ID of the task to check

**Response:**
- `200 OK`: Task status retrieved
- `404 Not Found`: Task not found

**Example Response (In Progress):**
```json
{
  "status": "pending",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Meme generation in progress"
}
```

**Example Response (Completed):**
```json
{
  "status": "completed",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Meme generated successfully",
  "data": {
    "text": "When you realize you forgot to add the off switch to the AI",
    "gif_url": "https://media.giphy.com/media/example.gif",
    "public_url": "https://example.supabase.co/storage/v1/object/public/memes/123.json"
  }
}
```

## Meme Generation Process

1. **Text Generation**: Uses GPT-3.5 to generate witty, context-appropriate meme text
2. **Keyword Extraction**: Extracts 2-3 relevant keywords from the generated text
3. **GIF Search**: Searches Giphy for a relevant GIF using the extracted keywords
4. **Storage**: Stores the meme data in Supabase with a public URL
5. **Response**: Returns the generated meme data including text, GIF URL, and public URL

## Rate Limiting

- 10 requests per minute per user
- 100 requests per hour per user

## Error Handling

Common error responses include:

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side error

## Example Workflow

1. **Generate a Meme**
   ```http
   POST /api/memes/generate
   Authorization: Bearer <token>
   Content-Type: application/json
   
   {
     "headline": "AI takes over the world",
     "analysis": "Analysis shows AI development is accelerating",
     "style": "funny"
   }
   ```

2. **Check Status**
   ```http
   GET /api/memes/status/550e8400-e29b-41d4-a716-446655440000
   Authorization: Bearer <token>
   ```

3. **View Meme**
   The generated meme can be accessed at the `public_url` returned in the status response.

## Environment Variables

The following environment variables must be set for the meme generation to work:

- `OPENAI_API_KEY`: API key for OpenAI
- `GIPHY_API_KEY`: API key for Giphy
- `SUPABASE_URL`: URL of your Supabase project
- `SUPABASE_KEY`: API key for Supabase
- `REDIS_URL`: URL for Redis (for Celery task queue)

## Dependencies

- OpenAI Python Client: For text generation
- Giphy API: For GIF search
- Supabase: For data storage
- Celery: For async task processing
- Redis: As the message broker for Celery

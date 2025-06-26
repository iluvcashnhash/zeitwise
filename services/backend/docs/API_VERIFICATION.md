# Verification API Reference

This document provides detailed information about the verification endpoints available in the ZeitWise API.

## Base URL

All endpoints are prefixed with `/api/verification`.

## Authentication

All endpoints require authentication using a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### 1. Check Verification Status

Check the verification status of a user's email or phone number.

```http
GET /status/{verification_type}
```

**Path Parameters:**
- `verification_type` (required): Type of verification to check (`email` or `phone`)

**Response:**
- `200 OK`: Verification status retrieved successfully
- `400 Bad Request`: Invalid verification type
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: User not found

**Example Request:**
```http
GET /api/verification/status/email
Authorization: Bearer your-jwt-token
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "type": "email",
    "is_verified": true,
    "verified_at": "2023-06-26T10:30:00Z",
    "contact": "user@example.com",
    "provider": "email"
  }
}
```

### 2. Resend Verification

Resend a verification email or SMS to the user.

```http
POST /resend
```

**Request Body:**
- `verification_type` (required): Type of verification to resend (`email` or `phone`)
- `redirect_url` (optional): URL to redirect to after verification (email only)

**Response:**
- `200 OK`: Verification email/SMS sent successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: User not found
- `429 Too Many Requests`: Too many verification attempts

**Example Request:**
```http
POST /api/verification/resend
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "verification_type": "email",
  "redirect_url": "https://yourapp.com/verify-success"
}
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "message": "Verification email sent",
    "contact": "user@example.com",
    "type": "email"
  }
}
```

### 3. Verify Phone with OTP

Verify a phone number using the OTP (One-Time Password) received via SMS.

```http
POST /verify-phone
```

**Request Body:**
- `phone` (required): Phone number with country code (e.g., +1234567890)
- `token` (required): OTP token received via SMS

**Response:**
- `200 OK`: Phone number verified successfully
- `400 Bad Request`: Invalid or expired OTP
- `404 Not Found`: User not found

**Example Request:**
```http
POST /api/verification/verify-phone
Content-Type: application/json

{
  "phone": "+1234567890",
  "token": "123456"
}
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "message": "Phone number verified successfully",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "phone": "+1234567890",
    "is_verified": true
  }
}
```

## Error Responses

All error responses follow the same format:

```json
{
  "detail": "Error message describing the issue"
}
```

### Common Error Status Codes

- `400 Bad Request`: Invalid request data or parameters
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Requested resource not found
- `409 Conflict`: Resource conflict (e.g., email already in use)
- `422 Unprocessable Entity`: Validation error in request data
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side error

## Rate Limiting

Verification endpoints are rate-limited to prevent abuse:

- Email verification: 5 requests per hour per user
- Phone verification: 3 requests per hour per phone number

## Security Considerations

- Always use HTTPS for all API requests
- Never expose your API keys or authentication tokens in client-side code
- Store JWT tokens securely (e.g., HTTP-only cookies)
- Implement proper error handling in your application
- Keep your dependencies up to date

## Support

For support or questions about the verification API, please contact our support team at support@zeitwise.com.

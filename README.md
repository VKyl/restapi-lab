# Lab project description

## Website topic: Music forum

## Music forum will have core pages

- Articles
- Events
- Find Band

## Articles page

Music forum users can read and create wiki pages about artists, add changes to existing ones. All changes (including article creation)

## Events page

On events page visitors can view or create musical event announcements. Users are able to view more details about event on event's own page

## Find Band

Page to find people to play with. Users with `I want to find a band` tick in their profile appear on that page for other user's searches.
Displayed with short information of instruments they play on, their favourite bands, their name or nickname, location where they are available to play.
To see detailed info on a user we can navigate to his profile

## User profile

On this page profile owner can configure his nickname (which must be unique across the platform), favorite bands and their intruments, band availability and location.

For view all the information above is available, plus articles that were written/participated by the person.

## Core Endpoints

### Authentication

`GET` endpoints are public. `POST`, `PUT` and `DELETE` endpoints require the access token from register, login or refresh:

```text
Authorization: Bearer <token>
```

Missing, invalid or expired token returns `401`. Only the event creator can change or delete an event, and only the article author can delete an article; otherwise `403`. Creating or editing an article adds the user to its contributors.

### Artists

`GET` /kmartists/artists/ - Get articles about artists. Has pagination and basic filters like genre and search query

Request params:

```json
    {
        "take": number,
        "skip": number,
        "genre": string,
        "search_query": string
    }
```

Response body:

```json
    {
        "items": { "id": string, "artist": string, "genres": string[] }[],
        "pagination": { "current_page": number, "total_pages": number, "total_records": number }
    }
```

`GET` /kmartists/artists/{id}/ - Get specific artist article.

Response body:

```json
    {
        "id": string,
        "artist": string,
        "genres": string[],
        "body": { "title": string, "content": string }[],
        "author": { "id": string, "name": string } | null,
        "contributors": { "id": string, "name": string }[],
        "created_at": string,
        "updated_at": string
    }
```

`POST` /kmartists/artists/ - Create an article about artist.

Request body:

```json
    {
        "artist": string,
        "genres": string[],
        "body": { "title": string, "content": string }[]
    }
```

Response body:

```json
    {
        "id": string
    }
```

`PUT` /kmartists/artists/{id}/ - Make edits to existing artist article

Request body:

```json
    {
        "genres": string[],
        "body": { "title": string, "content": string }[]
    }
```

`DELETE` /kmartists/artists/{id}/ - Delete artist article

### Genres

`GET` /kmartists/genres/ - Get all unique genres used in artist articles, sorted alphabetically. Used to build the genre filter.

Response body:

```json
    {
        "items": string[]
    }
```

### Events

`GET` /kmartists/events/ - list events

Request params:

```json
    {
        "take": number,
        "skip": number,
        "search_query": string,
        "location": string,
        "date": string
    }
```

Response body:

```json
    {
        "items": { "id": string, "name": string, "date": string, "location": string }[],
        "pagination": { "current_page": number, "total_pages": number, "total_records": number }
    }
```

`GET` /kmartists/events/{id}/ - Get specific event detailed info

Response body:

```json
    {
        "id": string,
        "name": string,
        "date": string,
        "location": string,
        "description": string,
        "contact_info": string,
        "creator": { "id": string, "name": string },
        "created_at": string,
        "updated_at": string
    }
```

`POST` /kmartists/events/ - Create new music event announcement

Request body:

```json
    {
        "name": string,
        "date": string,
        "location": string,
        "description": string,
        "contact_info": string
    }
```

Response body:

```json
    {
        "id": string
    }
```

`PUT` /kmartists/events/{id}/ - Make changes to event (available only for event creator)

Request body:

```json
    {
        "name": string,
        "date": string,
        "location": string,
        "description": string,
        "contact_info": string
    }
```

`DELETE` /kmartists/events/{id}/ - Delete event

### Auth

`POST` /kmartists/register/ - Register a new user. `first_name` and `last_name` are optional. Username must not contain `@`. Password must be at least 8 characters long and contain a lowercase letter, an uppercase letter and a digit.

Request body:

```json
    {
        "username": string,
        "first_name": string,
        "last_name": string,
        "email": string,
        "password": string,
        "password_confirmation": string
    }
```

Request body for users signing up with Microsoft. `microsoft_token` is the ID token issued by Microsoft for this app (`MICROSOFT_CLIENT_ID`); email is taken from the token, password is not needed.

```json
    {
        "username": string,
        "first_name": string,
        "last_name": string,
        "microsoft_token": string
    }
```

Response body:

```json
    {
        "token": string,
        "refresh_token": string
    }
```

`POST` /kmartists/login/ - Log in with username or email and password. `login` is treated as an email when it contains `@`, otherwise as a username

Request body:

```json
    {
        "login": string,
        "password": string
    }
```

Request body for users who registered with Microsoft. Returns `404` when no user is registered with this Microsoft account.

```json
    {
        "microsoft_token": string
    }
```

Response body:

```json
    {
        "token": string,
        "refresh_token": string
    }
```

`POST` /kmartists/refresh/ - Exchange a refresh token for a new pair of tokens

Request body:

```json
    {
        "refresh_token": string
    }
```

Response body:

```json
    {
        "token": string,
        "refresh_token": string
    }
```

Auth endpoints return JWTs signed with HS256 and payload `{ "id": string, "username": string, "first_name": string, "last_name": string, "type": "access" | "refresh", "iat": number, "exp": number }`. `token` is valid for 15 minutes, `refresh_token` for 7 days.

### Users

`GET` /kmartists/users/musicians/ - Get list of users available to play in band. When the request carries an access token, the requesting user is not included

Request params:

```json
    {
        "take": number,
        "skip": number,
        "location": string
    }
```

Response body:

```json
    {
        "items": {
            "id": string,
            "name": string,
            "instruments": string[],
            "favorite_bands": string[],
            "location": string
        }[],
        "pagination": { "current_page": number, "total_pages": number, "total_records": number }
    }
```

`GET` /kmartists/users/{id}/ - Get specific user profile

Response body:

```json
    {
        "id": string,
        "name": string,
        "instruments": string[],
        "favorite_bands": string[],
        "looking_for_band": boolean,
        "location": string
    }
```

`GET` /kmartists/users/{id}/articles/ - Get user's articles

Request params:

```json
    {
        "take": number,
        "skip": number
    }
```

Response body:

```json
    {
        "items": { "id": string, "artist": string, "genres": string[] }[],
        "pagination": { "current_page": number, "total_pages": number, "total_records": number }
    }
```

`PUT` /kmartists/users/{id}/ - Make changes to user profile (only for profile owner)

Request body:

```json
    {
        "name": string,
        "instruments": string[],
        "favorite_bands": string[],
        "looking_for_band": boolean,
        "location": string
    }
```

## Database diagram

![Database diagram](db_diagram.png)

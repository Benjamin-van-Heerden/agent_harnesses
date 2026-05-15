# Codebase and Structure

## Overview
{One paragraph: what this project is, what it does, who/what consumes it.}

## Tech Stack
{Bullet list: language(s), framework(s), key libraries, database(s), infrastructure. Only what matters for day-to-day development.}

## Directory Layout
{Annotated tree showing the top-level and important nested directories. For each directory, a brief description of what lives there. Do NOT list every file — focus on the organizational structure.}

## Key Modules
{For each significant module/component:
- What it does (1-2 sentences)
- Key files
- What it depends on / what depends on it}

## Data Flow
{How does data move through the system? Describe the primary paths — e.g. request comes in at X, gets routed to Y, hits the database via Z, response goes back through W. Cover the main flows, not every edge case.}

## Entry Points
{How is the application started? What commands, scripts, or processes are involved? Include dev and production if they differ.}

## External Interfaces
{APIs exposed, external services consumed, database connections, message queues, file system dependencies — anything that crosses the boundary of this codebase.}

## Conventions and Patterns
{Notable patterns used consistently in this codebase — e.g. "all API handlers follow the pattern X", "errors are handled via Y", "configuration is loaded from Z". Only include patterns that would help a new developer (or agent) write code that fits in.}

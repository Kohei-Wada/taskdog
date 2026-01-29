"""Base utilities for Mappers that convert DTOs/Entities to ViewModels.

Mappers are responsible for:
1. Converting Application layer DTOs to Presentation layer ViewModels
2. Extracting only the necessary fields from domain entities
3. Applying presentation logic (formatting, styling decisions)
4. Computing derived/display values

Design principles:
- Mappers are stateless (use static methods or module-level functions)
- Mappers contain presentation logic (strikethrough, status symbols, etc.)
- Mappers never modify domain entities or DTOs
"""

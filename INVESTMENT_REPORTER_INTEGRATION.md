# Investment + Reporter Agent Integration

## Overview

The investment analysis workflow now uses **two specialized agents** working together:

1. **Investment Agent** - Analyzes portfolio, provides recommendations
2. **Reporter Agent** - Converts analysis to professional PDF/PPTX reports

This separation of concerns eliminates duplicate code and leverages each agent's strengths.

## Configuration

Add both agents to your `agents.yaml`:

```yaml
agents:
  - name: investment-analyzer
    description: "Investment portfolio analysis and monitoring"
    plugin_type: investment
    mcp_port: 8005
    instructions:
      - "You are a financial analyst specialized in portfolio management."
      - "Analyze stocks, track portfolios, and provide actionable recommendations."
      - "Use format_portfolio_as_markdown to generate report content."
      
  - name: reporter
    description: "Professional report generator (PDF, PowerPoint, HTML)"
    plugin_type: reporter
    mcp_port: 8004
    instructions:
      - "You create professional reports from markdown and structured data."
      - "Convert markdown to PDF, PowerPoint, or HTML formats."
      - "Ensure reports are well-formatted and visually appealing."

teams:
  - name: investment-reporting
    description: "Complete investment analysis and reporting solution"
    members:
      - investment-analyzer
      - reporter
    instructions:
      - "Coordinate investment analysis with professional report generation."
      - "First use investment-analyzer to get portfolio data and format as markdown."
      - "Then use reporter to convert markdown to PDF or PowerPoint."
      - "Always show the user what will be in the report before generating."
```

## Workflow

### Step 1: Investment Analysis
The investment agent analyzes the portfolio:
```
User: "Analyze my portfolio and prepare a report"

Investment Agent uses:
- get_portfolio() - Gets current holdings
- format_portfolio_as_markdown() - Formats as markdown
```

### Step 2: Report Generation
The reporter agent converts to PDF:
```
Reporter Agent uses:
- markdown_to_pdf(markdown, output_path) - Creates professional PDF
```

## Example Usage

### Simple Portfolio Report

```python
# In Agent Hub chat:
"Create a PDF report of my investment portfolio"

# The team will:
# 1. Investment agent: Get portfolio data and format as markdown
# 2. Reporter agent: Convert markdown to PDF
# Result: Professional PDF report at specified location
```

### With Buy Opportunities

```python
"Create a portfolio report including buy opportunities in Technology and Healthcare sectors"

# The team will:
# 1. Investment agent: format_portfolio_as_markdown(
#       include_buy_opportunities=True,
#       sectors_for_opportunities=["Technology", "Healthcare"]
#    )
# 2. Reporter agent: markdown_to_pdf(...)
```

### PowerPoint Presentation

```python
"Create a PowerPoint presentation of my portfolio performance"

# The team will:
# 1. Investment agent: format_portfolio_as_markdown()
# 2. Reporter agent: markdown_to_pptx(...)
```

## What Changed

### Before (Single Agent with Duplicate Logic)

```python
# egile-mcp-reporter had create_investment_report()
# Problems:
# ✗ Domain-specific logic in generic reporter
# ✗ Markdown in PDF = unreadable
# ✗ Duplicate formatting code
# ✗ Tight coupling
```

### After (Two Agents, Single Responsibility)

```python
# Investment MCP: format_portfolio_as_markdown()
# - Knows investment domain
# - Formats data properly
# - Returns clean markdown

# Reporter MCP: markdown_to_pdf()
# - Knows document formatting
# - Proper markdown rendering
# - Reusable for any content

# Benefits:
# ✓ Clean separation of concerns
# ✓ Proper markdown → PDF conversion
# ✓ Reusable components
# ✓ Easy to maintain
```

## New Investment MCP Tool

### format_portfolio_as_markdown

Formats portfolio data as professional markdown suitable for PDF generation.

**Parameters:**
- `include_buy_opportunities` (boolean): Include buy opportunity analysis
- `sectors_for_opportunities` (array): Sectors to search for opportunities

**Returns:**
Markdown-formatted text with:
- Portfolio summary (total value, P/L, etc.)
- Holdings table with all positions
- Sell recommendations (for positions with sell score ≥ 6)
- Optional buy opportunities

**Example:**
```python
{
  "tool": "format_portfolio_as_markdown",
  "arguments": {
    "include_buy_opportunities": true,
    "sectors_for_opportunities": ["Technology", "Healthcare"]
  }
}
```

## Reporter MCP Tools (Existing)

### markdown_to_pdf

Converts markdown to professionally formatted PDF.

**Example:**
```python
{
  "tool": "markdown_to_pdf",
  "arguments": {
    "markdown": "# My Report\n\n## Section 1...",
    "output_path": "reports/portfolio_2026-01-15.pdf",
    "title": "Investment Portfolio Report"
  }
}
```

### markdown_to_pptx

Converts markdown to PowerPoint (## creates new slides).

**Example:**
```python
{
  "tool": "markdown_to_pptx",
  "arguments": {
    "markdown": "# Title\n\n## Slide 1\n\nContent...",
    "output_path": "reports/portfolio.pptx",
    "title": "Portfolio Analysis"
  }
}
```

## Benefits of This Approach

1. **Proper Formatting**: Markdown is correctly rendered to PDF/PPTX
2. **Reusability**: Reporter agent can be used for any content type
3. **Maintainability**: Each agent has clear, single responsibility
4. **Flexibility**: Easy to add new report types or formats
5. **No Duplication**: Investment logic stays in investment agent

## Migration Notes

If you were using the old `create_investment_report` in egile-mcp-reporter:

**Old way:**
```python
create_investment_report(portfolio_data, output_format="pdf")
```

**New way (in agent chat):**
```
"Format my portfolio as a report and save it as PDF"
```

The agent team will handle the coordination automatically!

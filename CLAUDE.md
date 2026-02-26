# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Executive Summary

The Metrics Django Application is an admin-style dashboard for monitoring software development processes, including team/developer velocity and other metrics. It follows a **Modular Monolith** architecture with **Hexagonal Architecture** principles.

### Key Principles
- **Readability First**: Code must be readable and easy to understand above all else
- **Module Boundaries**: Strict separation between modules via public APIs only
- **Domain-Driven Design**: Use nested objects that reflect business concepts
- **Semantic HTML + Bulma**: Frontend built with semantic HTML, Bulma CSS, and htmx
- **sd-metrics-lib Integration**: Leverage the core metrics library rather than rebuilding functionality

### Architecture Overview
- **4 Main Modules**: `tasks`, `forecast`, `velocity`, `ui_web`
- **Communication**: Modules communicate only through public APIs in `app/api/`
- **Data Federation**: `ui_web` module acts as gateway, combining data from other modules
- **External Integration**: JIRA/Azure DevOps via sd-metrics-lib

### Quick Reference

**Commands**: `python manage.py runserver 8002`, `python manage.py check`, `python manage.py migrate`
**Key Files**: `defaults_metrics.py`, `container.py`, `federated_data_fetcher.py`, `.env`
**Patterns**: API Repository, Component Facades, Domain Nesting, FederatedDataFetcher
**Modules**: `tasks/`, `forecast/`, `velocity/`, `ui_web/` - communicate via `app/api/`

---

## 1. Code Philosophy & Standards

### Development Philosophy

1. **Readability First**: Code must be readable and easy to understand above all else
2. **Extensibility Second**: After readability, code should be easy to extend and modify
3. **Performance Third**: Performance is the last consideration, after readability and extensibility

### Code Standards

- **Never write any code comments in production code** - code should be self-documenting through clear naming
- **Always use `@dataclass(slots=True)`** for all dataclasses to optimize memory usage
- **Review existing files** before creating new ones to avoid duplicating functionality
- **Import statements only at the top** - never use imports inside functions or methods
- **Use descriptive variable and method names** that reveal intent
- **Follow Single Responsibility Principle** - each function/class has one clear purpose
- **Apply Single Level of Abstraction Principle** - maintain consistent abstraction levels within functions, classes, modules, and system composition

### Domain-Driven Object Structure

Use nested objects that reflect business concepts rather than flat attribute lists:

**✅ Good: Nested Domain Objects**
```python
@dataclass(slots=True)
class Assignment:
    assignee: Optional[User] = None
    team: Optional[Team] = None

@dataclass(slots=True)
class Task:
    id: str
    title: str
    assignment: Assignment
    time_tracking: TimeTracking
    system_metadata: SystemMetadata
```

**❌ Bad: Flat Attributes**
```python
@dataclass(slots=True)
class Task:
    id: str
    title: str
    assignee_id: Optional[str] = None
    team_id: Optional[str] = None
    total_spent_time: Optional[float] = None
```

---

## 2. Architecture Overview

### Modular Monolith with Hexagonal Architecture

This application uses a **Modular Monolith** pattern with **Hexagonal Architecture** principles:

- **4 Self-Contained Modules**: `tasks`, `forecast`, `velocity`, `ui_web`
- **Strict Module Boundaries**: Communication only through public APIs in `app/api/`
- **UI Federation Gateway**: `ui_web` module combines data from other modules
- **External Integration**: JIRA/Azure DevOps via sd-metrics-lib

### Module Structure

Each module follows identical structure:
```
{module_name}/
├── app/
│   ├── api/                    # Public interfaces (what module provides)
│   ├── domain/                 # Core business logic
│   │   ├── model/             # Domain models and config
│   │   └── {domain}_service.py # Domain services
│   └── spi/                   # Dependencies (what module needs)
├── out/                       # External integrations
├── config_loader.py           # Settings loader
└── container.py              # DI container and module interface
```

### Naming Conventions
- **API Interfaces**: `ApiFor{Domain}` (e.g., `ApiForTaskSearch`, `ApiForForecast`, `ApiForVelocityCalculation`)
- **Domain Services**: `{Domain}Service`
- **Repository Interfaces**: `{Domain}Repository`
- **Repository Implementations**: `{External}{Domain}Repository`

### Data Flow
1. **Request** → Django URLs → Views
2. **Views** → Controllers → `FederatedDataFetcher`
3. **FederatedDataFetcher** → Module APIs → Domain Services
4. **Domain Services** → Repositories → External APIs (JIRA/Azure)

---

## 3. Key Architectural Patterns

### 1. API Repository Pattern
Modules communicate via repositories that call other modules' public APIs:

```python
# forecast/out/tasks_api_repository.py
class TasksApiRepository(TaskRepository):
    def __init__(self, task_search_api):
        self._task_search_api = task_search_api
    
    async def search(self, criteria) -> List[Task]:
        return await self._task_search_api.search(criteria)
```

### 2. Federated Data Fetcher
UI layer orchestrates concurrent data collection and enrichment:

```python
tasks = await (
    FederatedDataFetcher
    .for_(lambda: self._get_all_tasks())
    .with_foreach_populator(self.forecast_api.populate_estimations)
    .with_result_post_processor(self._sort_tasks_by_health_status)
    .fetch()
)
```

### 3. Component-Based UI Facades

Each UI component (chart, filter, table) is backed by a separate facade method. Think of facades as REST API endpoints - each returns data for one specific component.

**✅ Good: Separate methods per component**
```python
class TeamVelocityFacade:
    async def get_velocity_chart_data(self) -> Optional[ChartData]:
        # Chart component data
        
    def get_member_groups_data(self) -> List[MemberGroupData]:
        # Filter component data
```

**❌ Bad: Monolithic methods**
```python
async def get_velocity_data(self) -> VelocityData:
    # Mixed data for multiple components - if one fails, all fail
```

### 4. View Implementation Pattern

Views act like frontend controllers, making multiple facade calls and handling presentation logic:

```python
class TeamVelocityView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            # Independent component data fetching
            context["velocity_chart"] = asyncio.run(self.facade.get_velocity_chart_data())
            context["member_groups"] = self.facade.get_member_groups_data()
            context["success"] = True
        except Exception as e:
            # Graceful degradation
            context["velocity_chart"] = None
            context["member_groups"] = []
            context["success"] = False
            context["error"] = str(e)

        return context
```

### 5. HTMX Partial Chart Views

Charts are implemented as independently loadable htmx partials, each with its own URL endpoint, view class, and template. This enables dynamic chart updates (e.g., toggling rolling averages or filters) without full page reloads.

**URL Pattern**: `partials/{dashboard}/chart/`
**View Pattern**: Dedicated `TemplateView` subclass per chart partial
**Template Pattern**: `partials/{chart_name}.html` included in parent content templates

Example endpoints:
- `partials/dev-velocity/chart/` — Developer velocity chart
- `partials/dev-velocity/sp-chart/` — Developer story points chart
- `partials/team-velocity/chart/` — Team velocity chart

Query parameters supported by chart partials:
- `member_group_id` — Filter by team/member group
- `rolling_avg` — Rolling average window size (integer, e.g., `3` for 3-month average)
- `all_tasks` — Include unfinished tasks (`true`/`false`, dev velocity only)

---

## 4. Dependencies & Integration

### Core Dependencies
- **Django 6.0.2**: Web framework and admin interface
- **sd-metrics-lib[azure,jira] 7.0.1**: Core metrics calculation library
- **django-compressor 4.6.0**: Static file compression
- **environs 14.6.0**: Environment variable parsing

### sd-metrics-lib Integration

The `sd-metrics-lib` is central to this project. Always prefer library components over custom implementations.

**Architecture Pattern**: Calculators + Sources
1. Configure a `TaskProvider` (JIRA/Azure)
2. Configure extractors (`StoryPointExtractor`, `WorklogExtractor`)
3. Provide to calculators (`UserVelocityCalculator`, `GeneralizedTeamVelocityCalculator`)

**Key Components**:
- **Query Builders**: `JiraSearchQueryBuilder`, `AzureSearchQueryBuilder`
- **Task Providers**: `JiraTaskProvider`, `AzureTaskProvider`, `CachingTaskProvider`
- **Calculators**: `UserVelocityCalculator`, `GeneralizedTeamVelocityCalculator`

**Important**: Use modern `Task*` naming convention, never legacy `Issue*` names.

---

## 5. Configuration

### Environment Variables

Configuration is loaded via environment variables using the `environs` library.

#### Core Configuration
- `METRICS_TASK_TRACKER`: 'jira' or 'azure'
- `METRICS_BASE_URL`: Base URL for the application (deployment)
- `METRICS_BASIC_AUTH_USERS`: JSON dict for HTTP basic authentication

#### JIRA Configuration
- `METRICS_JIRA_SERVER_URL`: JIRA server URL
- `METRICS_JIRA_EMAIL`: JIRA user email
- `METRICS_JIRA_API_TOKEN`: JIRA API token
- `METRICS_STORY_POINT_CUSTOM_FIELD_ID`: Custom field ID for story points

#### Azure DevOps Configuration
- `METRICS_AZURE_ORGANIZATION_URL`: Azure DevOps organization URL
- `METRICS_AZURE_PAT`: Personal Access Token
- `METRICS_AZURE_PROJECT`: Project name

#### Status Code Mappings
- `METRICS_IN_PROGRESS_STATUS_CODES`: List of in-progress statuses (default: ['Analysis', 'Active', 'In Progress', 'In Development', 'QA', 'Validation', 'Testing', 'Review'])
- `METRICS_PENDING_STATUS_CODES`: List of pending/blocked statuses (default: ['Blocked', 'On Hold', 'Pending', 'Waiting'])
- `METRICS_DONE_STATUS_CODES`: List of completion statuses (default: ['Done', 'Closed', 'Resolved'])

#### Filtering & Projects
- `METRICS_PROJECT_KEYS`: List of project keys to include
- `METRICS_GLOBAL_TASK_TYPES_FILTER`: List of task types to include
- `METRICS_GLOBAL_TEAM_FILTER`: List of teams to include

#### Calculation Parameters
- `METRICS_WORKING_DAYS_PER_MONTH`: Working days per month (default: 22)
- `METRICS_IDEAL_HOURS_PER_DAY`: Ideal work hours per day (default: 4.0)
- `METRICS_STORY_POINTS_TO_IDEAL_HOURS_CONVERTION_RATIO`: Conversion ratio (default: 1.0)
- `METRICS_RECENTLY_FINISHED_TASKS_DAYS`: Days to consider for recent tasks (default: 14)

#### Team & Member Configuration
- `METRICS_MEMBERS`: JSON configuration of team members with levels and groups
- `METRICS_SENIORITY_LEVELS`: JSON dict of seniority multipliers (default: {"senior": 1.0, "middle": 2.0, "junior": 4.0})
- `METRICS_STAGES`: JSON configuration of workflow stages
- `METRICS_MEMBER_GROUP_CUSTOM_FILTERS`: JSON dict mapping member group IDs to custom JQL/query filters for task filtering (default: {})
  - Replaces default assignee-based filtering with custom query at the repository level
  - **JIRA example**: `{"TeamA": "parent in (PROJ-123, PROJ-456)"}`
  - **Azure example**: `{"TeamB": "[System.Parent] IN (174641, 176747)"}`
  - Works with both JIRA (JQL) and Azure DevOps (WIQL) query syntax
- `METRICS_MERGE_UNASSIGNED_INTO_FILTERED_GROUP`: When true, tasks with "Unassigned" member group are relabeled to the filtered group when viewing a specific member group (default: false)

#### Sorting Configuration
- `METRICS_DEFAULT_SORT_CRITERIA`: Default sorting criteria for tasks (default: '-health,-spent_time')
  - Supported criteria: priority, assignee, health, spent_time
  - Use '-' prefix for descending order
- `METRICS_STAGE_SORT_OVERRIDES`: JSON dict mapping stage names to custom sort criteria (default: {})
  - Overrides default sorting for specific workflow stages
  - **Example**: `{"Ready for Dev": "priority,assignee,-health"}`

#### Default Values
- `METRICS_DEFAULT_STORY_POINTS_VALUE_WHEN_MISSING`: Default story points when missing
- `METRICS_DEFAULT_SENIORITY_LEVEL_WHEN_MISSING`: Default seniority level (default: 'middle')
- `METRICS_DEFAULT_HEALTH_STATUS_WHEN_MISSING`: Default health status (default: 'GREEN')
- `METRICS_MEMBER_GROUP_WHEN_MISSING`: Default member group when unassigned
- `METRICS_DEFAULT_VELOCITY_TIME_UNIT`: Default time unit for velocity (default: 'DAY')

### Configuration Files

- `metrics/settings/defaults_metrics.py`: Application defaults
- `.env`: Environment-specific overrides (copy from `.env.example`)

### Configuration Classes
- Organize config classes by business domain (e.g., `JiraConfig`, `WorkflowConfig`)
- All defaults defined in `defaults_metrics.py`
- Config classes define structure only, not default values

```python
@dataclass(slots=True)
class TasksConfig:
    jira: JiraConfig
    workflow: WorkflowConfig
    member_velocity: MemberVelocityConfig
    sorting: SortingConfig
```

---

## 6. Frontend Guidelines

### Philosophy

Modern JavaScript-heavy frontend development is an anti-pattern. Instead, rely on semantic HTML, modern browser capabilities, and lightweight libraries.

### Core Principles

1. **Semantic HTML First**: Structure and functionality should work without CSS/JavaScript
2. **Minimize Custom JavaScript**: Avoid custom JS whenever possible - it's a design mistake
3. **Leverage Browser Native Features**: Prefer native HTML capabilities over JavaScript solutions

### Technology Stack

- **CSS Framework**: **Bulma** - Modern CSS framework with utility classes
    - Use Bulma's built-in components and utilities to minimize custom CSS
    - Leverage semantic HTML elements (`<article>`, `<nav>`, `<table>`, etc.)
    - Prefer Bulma classes over custom CSS when styling is needed

- **Interactivity**: **htmx** - HTML-centric approach to dynamic behavior
    - Use htmx for all dynamic interactions (AJAX, partial updates, etc.)
    - Avoid custom JavaScript libraries (React, Vue, Alpine.js)
    - Philosophy: Browsers should natively support htmx-like functionality

- **Data Visualization**: **Chart.js** + **chartjs-plugin-annotation** - Essential for dashboard metrics
    - Only JavaScript library exceptions due to project requirements
    - Use Chart.js for all charts, graphs, and data visualizations
    - Use chartjs-plugin-annotation for threshold/annotation overlays on charts

### Implementation Approach
- Start with semantic HTML structure
- Apply Bulma classes for styling
- Add htmx attributes for interactivity
- Use Chart.js only for data visualization needs

---

## 7. Testing Standards

### Core Testing Philosophy

- **Tests are living documentation** - write tests that explain business functionality in plain language
- **Use business behavior names** - pattern: `should<BusinessOutcome>When<BusinessCondition>`
- **Black-box testing only** - test inputs and outputs through public interfaces, never internal state
- **Structure tests with comments** - use `# Given # When # Then` to separate test phases visually
- **Single assertion per test** - each test validates one distinct business rule
- **Predefined input → expected output** - use realistic business examples, not arbitrary test data
- **Use domain language** - reference business concepts, not technical ones
- **Never use verify() or spy()** - avoid testing method calls or interaction patterns
- **Enable refactoring** - tests should survive implementation changes when behavior stays the same
- **Focus on end results** - test what the system does, not how it does it

### Test Structure

**Organize tests in multiple focused files per API:**
```
{module_name}/tests/
├── test_api_{domain}_health.py        # Health/status business rules
├── test_api_{domain}_calculation.py   # Core calculations/algorithms
├── test_api_{domain}_hierarchy.py     # Parent-child relationships/aggregations
├── test_api_{domain}_workflow.py      # Time-based operations/sequencing
├── test_api_{domain}_integration.py   # Multi-system interactions
├── test_api_{domain}_edge_cases.py    # Error conditions/boundary values
├── fixtures/{domain}_builders.py      # Business-focused data builders
└── mocks/mock_{spi_class}.py          # SPI dependency mocks only
```

### Test Responsibility Separation

**CRITICAL: Test at the appropriate level - avoid testing low-level logic through high-level APIs**
- **API Tests**: Integration, orchestration, business workflows, SPI coordination
- **Unit Tests**: Pure calculations, algorithms, mathematical formulas, validation rules
- **Never test calculator/utility classes through service APIs** - creates slow, complex tests
- **Each behavior tested once** - at the most appropriate level only

### Test Coverage Scope

**What to test:**
- **Domain services** (`app/domain/`) — API-level tests with mocked SPI dependencies
- **Facades** (`ui_web/facades/`) — API-level tests with mocked module APIs
- **Calculators** (`app/domain/calculation/`) — Unit tests, pure logic
- **Utility classes** (`ui_web/utils/`) — Unit tests, pure static methods
- **Extractors / Resolvers** — Unit tests, pure logic
- **Convertors with business logic** (`ui_web/convertors/`, `app/domain/convertors/`) — Unit tests when they contain calculations, filtering, or transformation logic

**What NOT to test:**
- **Views** — presentation controllers, no business logic
- **Containers** — DI wiring only
- **Adapter repositories** (`out/` layer) — thin delegation to module APIs
- **Data classes / Enums** — tested implicitly through their consumers
- **Templates** — HTML rendering, not business logic
- **Private methods directly** — always test through the public API of the owning class

### Business Behavior Testing Rules

**CRITICAL: Test business outcomes, not technical correctness**
- **Test business decisions and impacts** - Focus on outcomes that matter to stakeholders
- **Use domain scenarios** - Sprint planning, team retrospectives, capacity planning contexts
- **Avoid null/validation tests** - Focus on business edge cases, not technical implementation
- **Test decisions that matter** - Outcomes informing product managers, scrum masters, developers
- **Name tests as business stories** - Each test should read like a user story or requirement

### Mocking Strategy

**CRITICAL: Only mock SPI classes - never domain logic**
- ✅ Mock: `TaskRepository`, `VelocityRepository`, external APIs, adapters (anything in `app/spi/`)
- ❌ Never mock: Domain services, calculators, business rules (anything in `app/domain/`)

### Test Data

- **Use realistic business scenarios**: `critical_production_bug()`, `senior_developer_velocity()`  
- **Create fluent builders**: `TaskBuilder.authentication_feature().with_story_points(5.0).build()`
- **Predefined scenarios**: `BusinessScenarios.green_health_project()`, `red_health_project()`
- **Python unittest framework** with async support

---

## 8. Development Setup

### Environment Setup

1. **Activate virtual environment**: `source ~/.virtualenvs/metrics/bin/activate`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure environment**: Copy `.env.example` to `.env` and configure:
   - `METRICS_TASK_TRACKER`: 'jira' or 'azure'
   - Task tracker connection parameters (JIRA/Azure URLs, tokens)
   - `METRICS_MEMBERS`: JSON configuration of team members
   - Status codes and workflow configuration

### Development Commands

- **Run development server**: `python manage.py runserver 8002`
- **Verify configuration**: `python manage.py check`
- **Database migrations**: `python manage.py migrate`
- **Create superuser**: `python manage.py createsuperuser`
- **Run tests**: `pytest` (uses pytest as test runner for existing unittest tests)
- **Run specific test**: `pytest path/to/test_file.py::TestClass::test_method`

### Key Files & Components

#### UI Web Module Architecture

The `ui_web` module acts as a presentation layer and federation gateway, combining data from other modules using a component-based approach.

**Key Components**:

1. **Data Classes** (`ui_web/data/`): Define component data shapes, reuse across facades
2. **Facades** (`ui_web/facades/`): Act as component API endpoints  
3. **Convertors** (`ui_web/convertors/`): Transform domain objects to UI data
4. **Utils** (`ui_web/utils/`): Handle grouping, sorting, formatting in views

#### Error Handling

- **Facades**: Let exceptions bubble up (no try-catch)
- **Views**: Single try-catch around all facade calls for orchestration-level failures
- **Benefits**: Component independence, graceful degradation, better debugging

#### Important Files

- **Entry Points**: `metrics/urls.py` → `ui_web/urls.py`
- **Views**: `ui_web/views/` (package with `dev_velocity_view.py`, `team_velocity_view.py`, `current_tasks_view.py`, etc.)
- **Controllers**: `ui_web/controllers/` (business logic)
- **Templates**: `ui_web/templates/` (Bulma + htmx)
- **Configuration**: `metrics/settings/defaults_metrics.py`
- **Data Orchestration**: `ui_web/utils/federated_data_fetcher.py`
- **Module Interfaces**: Each module's `container.py`

---

## 9. Critical Reminders

1. **Enforce Module Boundaries**: Modules must **only** communicate via public APIs (`app/api/`). Use the API Repository Pattern for all inter-module data access.

2. **Keep Domain Logic Pure**: Never allow framework code (Django) or external dependencies in the `domain/` layer. Domain must be pure Python.

3. **Prioritize Readability**: Write simple, intention-revealing code. Each function should operate at a single level of abstraction.

4. **Leverage sd-metrics-lib**: Use library components over custom implementations. Embrace Calculators + Sources architecture.

5. **Use Domain-Driven Modeling**: Model data using nested objects that reflect business concepts rather than flat attributes.

6. **Security Guidelines**: Never expose or log secrets/keys in code. Never commit secrets to repository. Use environment variables for all sensitive configuration.
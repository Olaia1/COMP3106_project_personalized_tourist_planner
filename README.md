# Personalized Tourist Route Planner (Barcelona)

**COMP 3106 – Group 13**
Olaia Cortés (101427634) and Marta Zariquiegui (101427648)

## Overview

This project is an AI-based application that generates personalized tourist itineraries for Barcelona based on the user's interests, starting location, and available time. The problem is modeled as a state-space graph search: each state is a partial itinerary (visited attractions, current location, remaining time), and the goal is to maximize the user's total interest score while respecting a strict time budget that includes both visiting and walking times.

## How it works

1. **Dataset.** A simulated dataset of ~20 real Barcelona attractions (historical monuments, museums, parks, cultural landmarks) with their locations, estimated visiting times, ratings, touristic importance, and binary (0/1) category labels: history, art, architecture, nature, and local culture. Values are estimated or manually assigned using external sources such as Tripadvisor.
2. **Walking-time matrix.** Pairwise walking times between attractions, using Google Maps as a reference.
3. **User input.** The user provides a starting location, available time, and a rating for each category.
4. **Personalized scoring.** Each attraction receives a personalized score computed from the user's category preferences and the attraction's attributes.
5. **Route optimization.** Three search strategies are implemented and compared:
   - **Greedy Best-First Search:** fast, picks the most promising attraction at each step; not guaranteed optimal.
   - **Depth-First Search (DFS) with pruning:** explores combinations and orders with backtracking, discarding routes that exceed the time limit; optimal if fully explored but costly as the number of attractions grows.
   - **A\* Search:** uses an admissible and consistent heuristic estimating the score still achievable within the remaining time.

## Evaluation

- **Itinerary quality:** total accumulated interest score of the route.
- **Temporal efficiency:** adherence to the user's time limit.
- **Computational performance:** expanded nodes, memory usage, and execution time per algorithm.
- **Scenario testing:** different user profiles (e.g., history enthusiasts vs. architecture lovers) and time budgets (half-day vs. full-day).

## Repository structure

```
.
├── input_data/
│   ├── Barcelona_20_Attractions_With_Importance.xlsx   # Attractions with categories, ratings, visit times, and importance
│   └── Barcelona_Times_20_Attractions.xlsx             # Walking-time matrix between attractions
├── COMP3106_project_personalized_tourist_planner       # Project notebook / source code
└── README.md
```

> Update this section as files are added (e.g., search algorithm modules, user interface, report, and presentation).

## Project timeline

| Dates | Milestone |
|---|---|
| Nov 9–15 | Finalize dataset, attraction scores, and walking-time matrix; implement personalized scoring |
| Nov 16–22 | Implement and test Greedy Search and DFS with pruning |
| Nov 23–29 | Implement A\* (heuristic design and properties) and compare the three algorithms |
| Nov 30–Dec 6 | Analyze results, develop a simple user interface, write the report |
| Dec 7–11 | Finish the report and prepare the presentation |

## Requirements

To be completed (e.g., Python 3, pandas, openpyxl, matplotlib, Jupyter).

## Usage

To be completed.

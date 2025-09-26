# Design Document: Move-Based Player Scoring System

## 1. Overview

This document outlines the design for a new feature that calculates a post-game score for each player based on the quality of their individual moves. The goal is to provide players with deeper feedback on their performance beyond the simple win/loss/draw outcome, telling them *how well* they played.

The core concept is to leverage the same strategic evaluation logic used by the game's AI to analyze a player's moves after a game has concluded.

---

## 2. Brainstormed Scoring Approaches

Three potential methods for calculating a move-based score were considered.

### Option 1: "Move Optimality" Score (The Chess Engine Approach)

This method compares a player's actual move to the objectively "perfect" move as determined by a deep AI analysis.

*   **How it Works:**
    1.  After a game, the server replays it turn by turn.
    2.  At each step, it uses the full Minimax AI (for the standard 3x3 game) to find the single best move.
    3.  The player's move is then classified based on the change in the game's outcome (Win vs. Draw vs. Loss state).
        *   **Brilliant Move:** Maintains a winning/drawing position.
        *   **Inaccuracy:** Turns a winning position into a drawing one.
        *   **Blunder:** Turns a winning or drawing position into a losing one.

*   **Pros:**
    *   Provides the most accurate and objective measure of player skill.

*   **Cons:**
    *   **Extremely computationally expensive.** Running a full AI search for every move of a completed game is slow.
    *   **Not feasible for Ultimate Tic-Tac-Toe,** as the AI for that mode cannot determine the objectively perfect move due to the game's complexity.

### Option 2: "Heuristic Delta" Score (The Performance-Balanced Approach)

This method uses the AI's fast heuristic evaluation function to measure the change in strategic advantage caused by a player's move.

*   **How it Works:**
    1.  The server replays the game turn by turn.
    2.  Before a player's move, it calculates the board's heuristic value (`score_before`).
    3.  After the player's move, it calculates the new value (`score_after`).
    4.  The score for that move is the delta: `score_after - score_before`.
    5.  The player's final score is the sum of these deltas.

*   **Pros:**
    *   **Very fast and performant.** It reuses the AI's existing `_evaluate_board_heuristic` function without needing a deep search.
    *   Provides a strong and accurate measure of which player made strategically superior moves.
    *   Works for both standard and Ultimate game modes.

*   **Cons:**
    *   The raw score (e.g., "437") is not intuitive and requires normalization to be user-friendly.

### Option 3: "Strategic Achievements" Score (The Rule-Based Approach)

This method uses a simple, hard-coded set of rules to award points for specific, easily recognizable tactical plays.

*   **How it Works:**
    *   A checklist of moves is defined with arbitrary point values.
    *   Examples: Creating a fork (+25), blocking an opponent's threat (+8), taking the center square (+5).

*   **Pros:**
    *   The fastest and simplest method to implement.
    *   Transparent to the players.

*   **Cons:**
    *   Less nuanced; fails to capture subtle or long-term strategic moves.
    *   Point values are arbitrary and difficult to balance.

---

## 3. The Normalization Challenge

The recommended "Heuristic Delta" approach produces an unbounded score. To make this score meaningful, it must be normalized into a user-friendly range, such as 0 to 100.

Two methods for normalization were considered:

*   **Method A: Normalization Against a "Perfect Game"**
    *   This involves calculating the best and worst possible scores a player could have achieved in a specific game and grading their actual score against that range.
    *   **Problem:** This is even more computationally expensive than Option 1, as it requires checking every legal move at every turn to find the min/max possible scores.

*   **Method B: Mathematical Normalization (Sigmoid Function)**
    *   This uses a mathematical function (like the logistic function) to "squash" any unbounded number into a fixed range (e.g., 0 to 100).
    *   The formula `score = 100 / (1 + exp(-k * total_delta))` can be used.
    *   A scaling factor `k` is chosen to tune the curve, defining what raw score corresponds to a "good" normalized score (e.g., 90/100).
    *   **Benefit:** This is extremely fast, robust, and handles all score ranges gracefully.

---

## 4. Final Recommendation

The recommended path forward is a combination of the most balanced and performant options:

1.  **Scoring Method:** **Option 2: "Heuristic Delta" Score.** It provides a strategically accurate score for both game modes without compromising server performance.
2.  **Normalization Method:** **Method B: Mathematical Normalization (Sigmoid Function).** It is computationally cheap and effectively translates the raw heuristic score into an intuitive 0-100 performance rating for the player.

This combined approach will deliver a powerful and engaging new feature without introducing significant technical overhead.

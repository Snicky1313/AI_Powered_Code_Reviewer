#!/usr/bin/env python3
"""
AI-Powered Python Code Reviewer - SUS Survey Analysis Script

This script analyzes System Usability Scale (SUS) survey results from a CSV file.
The SUS is a 10-question survey that provides a reliable tool for measuring usability.

Author: Sagor Ahmmed
Created: 2025-09-28
"""

import pandas as pd
import sys
from typing import Dict, List


def calculate_sus_score(row: pd.Series) -> float:
    """
    Calculate the SUS score for a single user's responses.
    
    SUS Scoring Rules:
    - For odd-numbered questions (q1, q3, q5, q7, q9): score = user_response - 1
    - For even-numbered questions (q2, q4, q6, q8, q10): score = 5 - user_response
    - Sum all 10 scores and multiply by 2.5 to get final score (0-100)
    
    Args:
        row (pd.Series): A row from the survey DataFrame containing q1-q10 responses
        
    Returns:
        float: The calculated SUS score (0-100)
    """
    total_score = 0
    
    # Process odd-numbered questions (q1, q3, q5, q7, q9)
    for i in [1, 3, 5, 7, 9]:
        question_col = f'q{i}'
        if question_col in row:
            total_score += row[question_col] - 1
    
    # Process even-numbered questions (q2, q4, q6, q8, q10)
    for i in [2, 4, 6, 8, 10]:
        question_col = f'q{i}'
        if question_col in row:
            total_score += 5 - row[question_col]
    
    # Multiply by 2.5 to get final SUS score
    return total_score * 2.5


def get_sus_grade(score: float) -> str:
    """
    Convert a SUS score to a qualitative grade.
    
    SUS Grade Scale:
    - > 80.3: Excellent
    - > 68: Good
    - > 51: OK
    - <= 51: Poor
    
    Args:
        score (float): The SUS score (0-100)
        
    Returns:
        str: The qualitative grade
    """
    if score > 80.3:
        return "Excellent"
    elif score > 68:
        return "Good"
    elif score > 51:
        return "OK"
    else:
        return "Poor"


def analyze_survey_results(csv_file: str = "survey_results.csv") -> None:
    """
    Analyze SUS survey results from a CSV file and print comprehensive results.
    
    Args:
        csv_file (str): Path to the CSV file containing survey results
    """
    try:
        # Read the CSV file
        print(f"Loading survey data from {csv_file}...")
        df = pd.read_csv(csv_file)
        
        # Validate required columns
        required_columns = ['user_id'] + [f'q{i}' for i in range(1, 11)] + ['qualitative_feedback']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return
        
        # Validate that responses are in valid range (1-5)
        question_cols = [f'q{i}' for i in range(1, 11)]
        for col in question_cols:
            invalid_responses = df[(df[col] < 1) | (df[col] > 5)]
            if not invalid_responses.empty:
                print(f"Warning: Found invalid responses in {col} (should be 1-5):")
                print(invalid_responses[['user_id', col]])
        
        # Calculate SUS scores for each user
        print("Calculating SUS scores...")
        df['sus_score'] = df.apply(calculate_sus_score, axis=1)
        
        # Calculate statistics
        total_responses = len(df)
        average_score = df['sus_score'].mean()
        average_grade = get_sus_grade(average_score)
        
        # Print results
        print("\n" + "="*60)
        print("           SUS SURVEY ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\nTotal number of survey responses analyzed: {total_responses}")
        print(f"Average SUS score across all users: {average_score:.2f}")
        print(f"Qualitative grade for average score: {average_grade}")
        
        # Additional statistics
        print(f"\nDetailed Statistics:")
        print(f"  Minimum SUS score: {df['sus_score'].min():.2f}")
        print(f"  Maximum SUS score: {df['sus_score'].max():.2f}")
        print(f"  Standard deviation: {df['sus_score'].std():.2f}")
        
        # Grade distribution
        print(f"\nGrade Distribution:")
        grades = df['sus_score'].apply(get_sus_grade)
        grade_counts = grades.value_counts().sort_index()
        for grade, count in grade_counts.items():
            percentage = (count / total_responses) * 100
            print(f"  {grade}: {count} responses ({percentage:.1f}%)")
        
        # Qualitative feedback section
        print("\n" + "="*60)
        print("           QUALITATIVE FEEDBACK SUMMARY")
        print("="*60)
        
        # Filter out empty feedback
        feedback_df = df[df['qualitative_feedback'].notna() & 
                        (df['qualitative_feedback'].str.strip() != '')]
        
        if feedback_df.empty:
            print("No qualitative feedback provided.")
        else:
            print(f"Found {len(feedback_df)} feedback responses:\n")
            
            for idx, row in feedback_df.iterrows():
                user_id = row['user_id']
                sus_score = row['sus_score']
                feedback = row['qualitative_feedback'].strip()
                
                print(f"User: {user_id} (SUS Score: {sus_score:.1f})")
                print(f"Feedback: {feedback}")
                print("-" * 40)
        
        # Individual user scores (optional detailed view)
        print("\n" + "="*60)
        print("           INDIVIDUAL USER SCORES")
        print("="*60)
        
        print(f"{'User ID':<15} {'SUS Score':<10} {'Grade':<10}")
        print("-" * 35)
        
        for idx, row in df.iterrows():
            user_id = row['user_id']
            sus_score = row['sus_score']
            grade = get_sus_grade(sus_score)
            print(f"{user_id:<15} {sus_score:<10.1f} {grade:<10}")
            
    except FileNotFoundError:
        print(f"Error: Could not find the file '{csv_file}'.")
        print("Please ensure the survey_results.csv file exists in the current directory.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{csv_file}' is empty.")
    except pd.errors.ParserError as e:
        print(f"Error: Could not parse the CSV file. {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")


def create_sample_data() -> None:
    """
    Create a sample survey_results.csv file for testing purposes.
    This function is for demonstration only.
    """
    sample_data = {
        'user_id': ['user001', 'user002', 'user003'],
        'q1': [5, 4, 5],
        'q2': [1, 2, 1],
        'q3': [5, 5, 4],
        'q4': [2, 1, 1],
        'q5': [4, 5, 5],
        'q6': [1, 2, 1],
        'q7': [5, 4, 5],
        'q8': [2, 1, 1],
        'q9': [5, 4, 5],
        'q10': [1, 2, 1],
        'qualitative_feedback': [
            "The integration is seamless! I wish I could one-click apply the suggestions.",
            "Very helpful, but sometimes the AI comments are too long.",
            "Excellent tool, a real time-saver."
        ]
    }
    
    df = pd.DataFrame(sample_data)
    df.to_csv('survey_results.csv', index=False)
    print("Sample survey_results.csv file created successfully!")


if __name__ == "__main__":
    """
    Main execution block. 
    
    Usage:
        python analyze_usability.py                    # Analyze survey_results.csv
        python analyze_usability.py --create-sample    # Create sample data file
        python analyze_usability.py custom_file.csv    # Analyze custom CSV file
    """
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-sample":
            create_sample_data()
        else:
            # Custom CSV file provided
            csv_file = sys.argv[1]
            analyze_survey_results(csv_file)
    else:
        # Default behavior - analyze survey_results.csv
        analyze_survey_results()


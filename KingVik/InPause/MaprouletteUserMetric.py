import requests
import csv
import os
from datetime import datetime
from bs4 import BeautifulSoup
import time


class MapRouletteLeaderboard:
    def __init__(self, api_key=None):
        self.base_url = "https://maproulette.org"
        self.session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        if api_key:
            headers['apiKey'] = api_key
        self.session.headers.update(headers)

    def get_challenge_tasks(self, challenge_id):
        """Get all tasks for a challenge to calculate statistics"""
        url = f"{self.base_url}/api/v2/challenge/{challenge_id}/tasks"
        params = {'limit': 1000, 'page': 0}
        all_tasks = []

        try:
            while True:
                response = self.session.get(url, params=params)
                if response.status_code != 200:
                    print(f"Error getting tasks: {response.text}")
                    break

                tasks = response.json()
                if not tasks:
                    break

                all_tasks.extend(tasks)
                params['page'] += 1

                # Prevent infinite loops
                if len(tasks) < params['limit']:
                    break

            return all_tasks
        except Exception as e:
            print(f"Error fetching tasks: {str(e)}")
            return None

    def calculate_user_stats(self, tasks):
        """Calculate user statistics from task data"""
        user_stats = {}

        for task in tasks:
            if 'completionResponses' not in task:
                continue

            for response in task['completionResponses']:
                user_id = response.get('userId')
                user_name = response.get('username')
                status = response.get('status')

                if user_id not in user_stats:
                    user_stats[user_id] = {
                        'name': user_name,
                        'completed': 0,
                        'score': 0
                    }

                # Count completed tasks (status 1 = Fixed)
                if status == 1:
                    user_stats[user_id]['completed'] += 1
                    # Simple scoring - 1 point per completed task
                    user_stats[user_id]['score'] += 1

        return user_stats

    def get_leaderboard_data(self, challenge_id):
        """Get leaderboard data by analyzing task completion"""
        print(f"Processing challenge {challenge_id}...")

        # Get all tasks for the challenge
        tasks = self.get_challenge_tasks(challenge_id)
        if not tasks:
            print(f"No tasks found for challenge {challenge_id}")
            return []

        # Calculate user statistics
        user_stats = self.calculate_user_stats(tasks)
        if not user_stats:
            print(f"No user activity found for challenge {challenge_id}")
            return []

        # Convert to leaderboard format
        leaderboard = []
        for user_id, stats in user_stats.items():
            leaderboard.append({
                'Challenge ID': challenge_id,
                'User ID': user_id,
                'User Name': stats['name'],
                'Score': stats['score'],
                'Tasks Completed': stats['completed'],
                'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        # Sort by score (descending)
        leaderboard.sort(key=lambda x: x['Score'], reverse=True)

        # Add ranks
        for i, entry in enumerate(leaderboard, 1):
            entry['Rank'] = i

        print(f"Found {len(leaderboard)} active users for challenge {challenge_id}")
        return leaderboard

    def save_to_csv(self, data, output_path):
        """Save data to CSV file"""
        if not data:
            print("No data to save")
            return

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        fieldnames = [
            'Challenge ID', 'User ID', 'User Name', 'Rank',
            'Score', 'Tasks Completed', 'Last Updated'
        ]

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"Data successfully saved to {output_path}")


def main():
    # Configuration
    api_key = "11675|da56f36d-8460-486f-91dd-f095ac517c64"  # Replace with your actual API key
    challenge_ids = [52707, 52701]  # Challenge IDs to process
    output_path = "C:\\Users\\chukw\\OneDrive\\Documentos\\TomTom Event\\maproulette_leaderboard.csv"

    # Initialize
    mr = MapRouletteLeaderboard(api_key)
    results = []

    # Process each challenge
    for challenge_id in challenge_ids:
        leaderboard_data = mr.get_leaderboard_data(challenge_id)
        if leaderboard_data:
            results.extend(leaderboard_data)
        time.sleep(1)  # Be polite with API requests

    # Save results
    mr.save_to_csv(results, output_path)


if __name__ == "__main__":
    main()
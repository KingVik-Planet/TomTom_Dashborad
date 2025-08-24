import requests
import csv
import os
from datetime import datetime


class MapRouletteStats:
    def __init__(self, base_url="https://maproulette.org", api_key=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['apiKey'] = api_key
        self.session.headers.update(headers)
        self.task_status_map = {
            0: 'Available',
            1: 'Fixed',
            2: 'Already Fixed',
            3: 'False Positive',
            4: 'Skipped',
            5: 'Too Hard'
        }

    def get_challenge_info(self, challenge_id):
        """Get basic challenge information"""
        url = f"{self.base_url}/api/v2/challenge/{challenge_id}"
        resp = self.session.get(url)
        if resp.status_code == 200:
            return resp.json()
        print(f"Error getting challenge info: {resp.text}")
        return None

    def get_all_tasks(self, challenge_id):
        """Get all tasks for a challenge with pagination"""
        all_tasks = []
        page = 0
        limit = 1000  # Max per request

        while True:
            url = f"{self.base_url}/api/v2/challenge/{challenge_id}/tasks"
            params = {
                'limit': limit,
                'page': page
            }
            resp = self.session.get(url, params=params)

            if resp.status_code != 200:
                print(f"Error getting tasks page {page}: {resp.text}")
                break

            tasks = resp.json()
            if not tasks:
                break

            all_tasks.extend(tasks)
            page += 1

            # Stop if we got fewer tasks than requested (last page)
            if len(tasks) < limit:
                break

        return all_tasks

    def calculate_task_stats(self, tasks):
        """Calculate statistics from task data"""
        stats = {status_name: 0 for status_name in self.task_status_map.values()}
        stats['Total'] = len(tasks)

        for task in tasks:
            status = task.get('status')
            if status in self.task_status_map:
                stats[self.task_status_map[status]] += 1

        return stats

    def determine_status(self, stats):
        """Determine challenge status based on task completion"""
        if stats['Available'] == stats['Total']:
            return "Not Started"
        elif stats['Available'] == 0:
            return "Completed"
        else:
            return "In Progress"

    def process_challenge(self, challenge_id):
        """Process a single challenge and return its stats"""
        print(f"\nProcessing challenge {challenge_id}...")

        # Get basic challenge info
        info = self.get_challenge_info(challenge_id)
        if not info:
            return None

        # Get all tasks with pagination
        tasks = self.get_all_tasks(challenge_id)
        if not tasks:
            return None

        # Calculate statistics
        stats = self.calculate_task_stats(tasks)
        status = self.determine_status(stats)

        # Combine all data
        result = {
            'Challenge ID': challenge_id,
            'Name': info.get('name', ''),
            'Created': info.get('created', ''),
            'Modified': info.get('modified', ''),
            'Completion %': info.get('completionPercentage', 0),
            'Tasks Remaining': info.get('tasksRemaining', 0),
            'Total Tasks': stats['Total'],
            'Fixed': stats['Fixed'],
            'Already Fixed': stats['Already Fixed'],
            'False Positive': stats['False Positive'],
            'Skipped': stats['Skipped'],
            'Too Hard': stats['Too Hard'],
            'Available': stats['Available'],
            'Status': status,
            'Last Updated': datetime.now().strftime('%Y-%m-%d')
        }

        print(f"Stats for challenge {challenge_id}: {result}")
        return result

    def load_existing_data(self, out_file):
        """Load existing data from CSV if it exists"""
        if not os.path.exists(out_file):
            return []

        with open(out_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def save_csv(self, new_data, out_file):
        """Save data to CSV, appending to existing file while maintaining structure"""
        fields = [
            'Challenge ID', 'Name', 'Created', 'Modified', 'Completion %',
            'Tasks Remaining', 'Total Tasks', 'Fixed', 'Already Fixed',
            'False Positive', 'Skipped', 'Too Hard', 'Available', 'Status',
            'Last Updated'
        ]

        os.makedirs(os.path.dirname(out_file), exist_ok=True)

        # Load existing data
        existing_data = self.load_existing_data(out_file)

        # Filter out today's data if it exists
        today = datetime.now().strftime('%Y-%m-%d')
        existing_data = [row for row in existing_data
                         if not row['Last Updated'].startswith(today)]

        # Combine existing data with new data
        combined_data = existing_data + new_data

        # Write to CSV
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(combined_data)

        print(f"✅ Saved updated data at {out_file} (Total records: {len(combined_data)})")


def main():
    challenges = [
        52698, 52699, 52701, 52702, 52704, 52706, 52707, 52708, 52709, 52716  # AfricaFix90
    ]
    # out_folder = "C:\\Users\\chukw\\OneDrive\\Documentos\\TomTom Event"
    out_folder = "G:\My Drive\Dashboard\TomTom Power BI\MapRoulette"
    out_file = os.path.join(out_folder, "Maproulette_Daily_Stats.csv")

    # Replace with your actual API key
    api_key = "YOUR_API_KEY_HERE"

    stats = MapRouletteStats(api_key=api_key)
    results = []

    for challenge_id in challenges:
        challenge_stats = stats.process_challenge(challenge_id)
        if challenge_stats:
            results.append(challenge_stats)
            print(f"Processed {challenge_stats['Total Tasks']} tasks for challenge {challenge_id}")

    if results:
        stats.save_csv(results, out_file)
    else:
        print("No data was retrieved for any challenges")


if __name__ == "__main__":
    main()
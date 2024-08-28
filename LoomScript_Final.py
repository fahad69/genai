import requests
import json
import sys
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time

# Function to get specific cookies using Playwright
def get_specific_cookies():
    with sync_playwright() as p:
        user_data_dir = r'C:\\Users\\FAHAD MAQBOOL\\AppData\\Local\\Google\\Chrome\\User Data'
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            channel="chrome",
            args=[
                '--profile-directory=Profile 5',
                '--remote-debugging-port=9222'
            ]
        )

        time.sleep(3)

        if not browser.pages:
            print("No pages opened in the browser. Check the profile directory and ensure it's correct.")
            browser.close()
            return {}

        page = browser.pages[0]

        if page.url == "about:blank":
            print("Browser opened with 'about:blank'. Navigating to Loom manually.")
            page.goto('https://www.loom.com/looms/videos', wait_until='networkidle')

        if 'login' in page.url or "Login" in page.title():
            print("Redirection to login page detected. Please ensure you are logged in with the correct profile.")
            browser.close()
            return {}

        # Define the cookies we're interested in
        desired_cookies = {'connect.sid': None, 'loom-sst': None}

        def handle_request(route, request):
            nonlocal desired_cookies
            if "https://www.loom.com/graphql" in request.url:
                cookies = page.context.cookies()
                for cookie in cookies:
                    if cookie['name'] in desired_cookies:
                        desired_cookies[cookie['name']] = cookie['value']
                route.continue_()

        page.route("https://www.loom.com/graphql", handle_request)

        # Reload the page to capture requests
        page.reload()
        try:
            page.wait_for_load_state('networkidle', timeout=15000)
        except Exception as e:
            print(f"Error or timeout occurred while waiting for network idle: {e}")

        # Close the browser context
        browser.close()

        # Return only the cookies that we are interested in
        filtered_cookies = {key: value for key, value in desired_cookies.items() if value is not None}
        return filtered_cookies

# Set encoding to UTF-8 for Windows
def set_utf8_encoding():
    if os.name == 'nt':
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

set_utf8_encoding()

# Function to fetch video transcript
def fetch_video_transcript(video_id, cookies, headers):
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'FetchVideoTranscript',
        'variables': {
            'videoId': video_id,
        },
        'query': '''
        query FetchVideoTranscript($videoId: ID!) {
            fetchVideoTranscript(videoId: $videoId) {
                ... on VideoTranscriptDetails {
                    source_url
                    __typename
                }
                ... on GenericError {
                    message
                    __typename
                }
                __typename
            }
        }
        '''
    }

    try:
        response = requests.post(url, cookies=cookies, headers=headers, json=json_data)

        if response.status_code != 200:
            return {"error": f"Failed to fetch transcript for Video ID: {video_id}. HTTP Status Code: {response.status_code}"}

        response_json = response.json()

        transcript_data = response_json.get('data', {}).get('fetchVideoTranscript', {})

        if transcript_data.get('__typename') == 'VideoTranscriptDetails':
            source_url = transcript_data.get('source_url')
            if source_url:
                transcript_response = requests.get(source_url)
                if transcript_response.status_code == 200:
                    transcript_json = transcript_response.json()
                    phrases = transcript_json.get('phrases', [])
                    paragraph = " ".join([phrase.get('value', '') for phrase in phrases])
                    return {
                        "transcription_text": paragraph,
                        "phrases": [
                            {
                                "ts": phrase.get('ts'),
                                "value": phrase.get('value', '')
                            } for phrase in phrases
                        ]
                    }
                else:
                    return {"error": f"Failed to retrieve transcript text for Video ID: {video_id}. HTTP Status Code: {transcript_response.status_code}"}
            else:
                return {"error": f"No transcript available for Video ID: {video_id}"}
        elif transcript_data.get('__typename') == 'GenericError':
            error_message = transcript_data.get('message', 'Unknown error')
            return {"error": f"Error fetching transcript for Video ID: {video_id}: {error_message}"}
        else:
            return {"error": f"Unexpected response structure when fetching transcript for Video ID: {video_id}"}
    except Exception as e:
        return {"error": f"Exception occurred while fetching transcript for Video ID: {video_id}: {e}"}

# Function to fetch video description
def fetch_video_description(video_id, cookies, headers):
    try:
        url = f'https://www.loom.com/share/{video_id}'
        response = requests.get(url, cookies=cookies, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        description_meta = soup.find('meta', attrs={'name': 'description'})
        description = description_meta.get('content', 'No description found.') if description_meta else 'No description found.'

        return description
    except Exception as e:
        return f"Error fetching description for Video ID: {video_id}: {e}"

# Function to fetch video chapters
def fetch_video_chapters(video_id, cookies, headers):
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'FetchChapters',
        'variables': {
            'videoId': video_id,
            'password': None,
        },
        'query': '''
        query FetchChapters($videoId: ID!, $password: String) {
            fetchVideoChapters(videoId: $videoId, password: $password) {
                ... on VideoChapters {
                    id
                    video_id
                    content
                    __typename
                }
                ... on EmptyChaptersPayload {
                    content
                    __typename
                }
                ... on InvalidRequestWarning {
                    message
                    __typename
                }
                ... on Error {
                    message
                    __typename
                }
                __typename
            }
        }
        '''
    }

    try:
        response = requests.post(url, cookies=cookies, headers=headers, json=json_data)

        if response.status_code != 200:
            return {"error": f"Failed to fetch chapters for Video ID: {video_id}. HTTP Status Code: {response.status_code}"}

        response_json = response.json()

        chapters_content = response_json.get('data', {}).get('fetchVideoChapters', {}).get('content', '')
        chapters = []

        if chapters_content:
            chapter_lines = chapters_content.split('\n')
            for line in chapter_lines:
                if line.strip():  # Ignore empty lines
                    time_step, name = line.split(' ', 1)
                    chapters.append({"name": name, "time_step": time_step})

        return chapters
    except Exception as e:
        return f"Error fetching chapters for Video ID: {video_id}: {e}"

# Function to fetch video details and save them to a JSON file
def fetch_video_details(video_id, video_name, cookies, headers, base_path):
    details = {}

    # Fetch transcript
    transcript_info = fetch_video_transcript(video_id, cookies, headers)
    details['transcript_info'] = transcript_info

    # Fetch description
    description = fetch_video_description(video_id, cookies, headers)
    details['Summary'] = description

    # Fetch chapters
    chapters = fetch_video_chapters(video_id, cookies, headers)
    details['chapters'] = chapters

    file_path = os.path.join(base_path, f'{video_id}.json')

    video_details = {
        "video_id": video_id,
        "video_name": video_name,
        "details": details
    }

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(video_details, file, indent=4, ensure_ascii=False)

    return file_path

# Function to fetch only videos from the root folder
def fetch_videos_from_root(cookies, headers, base_path):
    json_data = {
        'operationName': 'GetLooms',
        'variables': {
            'limit': 50,
            'cursor': None,
            'folderId': None,  # None indicates the root folder
            'source': 'ALL',
            'sortOrder': 'DESC',
            'sortType': 'RECENT',
            'filters': [
                [
                    {
                        'type': 'CREATED_BY_ME',
                    },
                ],
                [
                    {
                        'type': 'NOT_IN_FOLDER',
                    },
                ],
            ],
            'timeRange': None,
        },
        'query': '''
        query GetLooms($limit: Int!, $cursor: String, $folderId: String, $sourceValue: String, $source: LoomsSource!, $sortType: LoomsSortType!, $sortOrder: LoomsSortOrder!, $sortGrouping: LoomsSortGrouping, $filters: [[LoomsCollectionFilter!]!], $timeRange: TimeRange) {
            getLooms {
                __typename
                ... on GetLoomsPayload {
                    videos(
                        first: $limit
                        after: $cursor
                        folderId: $folderId
                        sourceValue: $sourceValue
                        source: $source
                        sortType: $sortType
                        sortOrder: $sortOrder
                        sortGrouping: $sortGrouping
                        filters: $filters
                        timeRange: $timeRange
                    ) {
                        edges {
                            cursor
                            node {
                                id
                                name
                            }
                            __typename
                        }
                        pageInfo {
                            endCursor
                            hasNextPage
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        }
        '''
    }

    try:
        response = requests.post('https://www.loom.com/graphql', cookies=cookies, headers=headers, json=json_data)

        if response.status_code != 200:
            return []

        response_json = response.json()

        videos_data = response_json.get('data', {}).get('getLooms', {}).get('videos', {}).get('edges', [])

        videos = []
        for video in videos_data:
            video_node = video.get('node', {})
            video_id = video_node.get('id')
            video_name = video_node.get('name', 'Unnamed Video')

            if video_id:
                file_path = fetch_video_details(video_id, video_name, cookies, headers, base_path)
                videos.append({
                    "video_id": video_id,
                    "video_name": video_name,
                    "file_path": file_path
                })

        return videos
    except Exception as e:
        return []

# Function to fetch videos from a folder
def fetch_videos_from_folder(folder_id=None, cookies=None, headers=None, base_path=None):
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'GetLooms',
        'variables': {
            'limit': 50,
            'cursor': None,
            'folderId': folder_id,
            'source': 'ALL',
            'sortOrder': 'DESC',
            'sortType': 'RECENT',
        },
        'query': '''
        query GetLooms($limit: Int!, $cursor: String, $folderId: String, $source: LoomsSource!, $sortType: LoomsSortType!, $sortOrder: LoomsSortOrder!) {
            getLooms {
                ... on GetLoomsPayload {
                    videos(first: $limit, after: $cursor, folderId: $folderId, source: $source, sortType: $sortType, sortOrder: $sortOrder) {
                        edges {
                            node {
                                id
                                name
                            }
                        }
                    }
                }
            }
        }
        '''
    }

    try:
        response = requests.post(url, cookies=cookies, headers=headers, json=json_data)

        if response.status_code != 200:
            return []

        response_json = response.json()

        videos_data = response_json.get('data', {}).get('getLooms', {}).get('videos', {}).get('edges', [])

        videos = []
        for video in videos_data:
            video_node = video.get('node', {})
            video_id = video_node.get('id')
            video_name = video_node.get('name', 'Unnamed Video')

            if video_id:
                file_path = fetch_video_details(video_id, video_name, cookies, headers, base_path)
                videos.append({
                    "video_id": video_id,
                    "video_name": video_name,
                    "file_path": file_path
                })

        return videos
    except Exception as e:
        return []

# Recursively fetch folders and their contents
def fetch_folders(parent_folder_id=None, cookies=None, headers=None, base_path=None):
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'GetPublishedFolders',
        'variables': {
            'first': 50,
            'after': None,
            'source': 'ACTIVE',
            'sortOrder': 'DESC',
            'sortType': 'RECENT',
            'parentFolderId': parent_folder_id,
        },
        'query': '''
        query GetPublishedFolders($first: Int!, $after: String, $source: FolderSource!, $sortType: LoomsSortType!, $sortOrder: LoomsSortOrder!, $parentFolderId: String) {
            getPublishedFolders {
                ... on GetPublishedFoldersPayload {
                    folders(first: $first, after: $after, source: $source, sortType: $sortType, sortOrder: $sortOrder, parentFolderId: $parentFolderId) {
                        edges {
                            node {
                                id
                                name
                                hasSubFolders
                            }
                        }
                    }
                }
            }
        }
        '''
    }

    try:
        response = requests.post(url, cookies=cookies, headers=headers, json=json_data)

        if response.status_code != 200:
            return {}

        response_json = response.json()

        folders_data = response_json.get('data', {}).get('getPublishedFolders', {}).get('folders', {}).get('edges', [])

        # Fetch videos in the current folder (if we are not at the root level)
        if parent_folder_id:
            videos = fetch_videos_from_folder(folder_id=parent_folder_id, cookies=cookies, headers=headers, base_path=base_path)

        # Recursively fetch subfolders and their content
        for folder in folders_data:
            folder_node = folder.get('node', {})
            folder_id = folder_node.get('id')
            folder_name = folder_node.get('name', 'Unnamed Folder')
            has_sub_folders = folder_node.get('hasSubFolders', False)

            if folder_id:
                subfolder_path = os.path.join(base_path, folder_name)
                os.makedirs(subfolder_path, exist_ok=True)
                fetch_folders(folder_id, cookies, headers, base_path=subfolder_path)

        return {}
    except Exception as e:
        return {}

if __name__ == "__main__":
    # Get the dynamic cookies using Playwright
    # specific_cookies = get_specific_cookies()

    # if not specific_cookies:
    #     print("Failed to retrieve necessary cookies. Exiting.")
    #     sys.exit(1)
    
    specific_cookies={
    'connect.sid': 's%3AhT1UYCxLi2IpOqHOneNNGozXaYPyistf.Ksl%2FaDzsVwPtOw3xgcpIkYvQi%2BqedlYhrQgWNN7%2FG90',
    'loom-sst': 'lsst-0389a6bc-5ae3-45c5-9e07-568a3a821324',
}
    # Define headers with the dynamic cookies
    headers = {
        'accept': '*/*',
        'accept-language': 'en-PK,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,it;q=0.6',
        'apollographql-client-name': 'web',
        'apollographql-client-version': '2564a2c',
        'content-type': 'application/json',
        'origin': 'https://www.loom.com',
        'referer': 'https://www.loom.com/looms/videos',
        'sec-fetch-mode': 'cors',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'x-loom-request-source': 'loom_web_2564a2c',
    }

    # Define the base directory for the output
    base_output_dir = 'Loom_Data'
    os.makedirs(base_output_dir, exist_ok=True)

    # Fetch the root videos
    fetch_videos_from_root(specific_cookies, headers, base_output_dir)

    # Fetch all folders and their nested contents
    fetch_folders(parent_folder_id=None, cookies=specific_cookies, headers=headers, base_path=base_output_dir)

    print(f"Folder structure and JSON files created under {base_output_dir}")

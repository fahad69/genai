import requests
import json
import sys
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
from datetime import datetime

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
            page.goto('https://www.loom.com/looms/spaces', wait_until='networkidle')

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

# Define cookies and headers for requests
# cookies = get_specific_cookies()
cookies = {
    'connect.sid': 's%3AhT1UYCxLi2IpOqHOneNNGozXaYPyistf.Ksl%2FaDzsVwPtOw3xgcpIkYvQi%2BqedlYhrQgWNN7%2FG90',
    'loom-sst': 'lsst-0389a6bc-5ae3-45c5-9e07-568a3a821324',
}
headers = {
    'accept': '*/*',
    'accept-language': 'en-PK,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,it;q=0.6',
    'apollographql-client-name': 'web',
    'apollographql-client-version': '14a990c',
    'content-type': 'application/json',
    'origin': 'https://www.loom.com',
    'priority': 'u=1, i',
    'referer': 'https://www.loom.com/spaces/All-Fahads-Workspace-30463902',
    'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'x-loom-request-source': 'loom_web_14a990c',
}

def fetch_video_transcript(video_id):
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'FetchVideoTranscript',
        'variables': {'videoId': video_id},
        'query': '''
        query FetchVideoTranscript($videoId: ID!) {
            fetchVideoTranscript(videoId: $videoId) {
                ... on VideoTranscriptDetails {
                    source_url
                    createdAt
                    language
                }
                ... on GenericError {
                    message
                }
            }
        }
        '''
    }
    try:
        response = requests.post(url, cookies=cookies, headers=headers, json=json_data)
        response.raise_for_status()
        response_json = response.json()
        transcript_data = response_json.get('data', {}).get('fetchVideoTranscript', {})
        
        if 'source_url' in transcript_data:
            created_at = transcript_data.get('createdAt')
            language = transcript_data.get('language')
            formatted_created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S") if created_at else 'Unknown'
            
            transcript_response = requests.get(transcript_data['source_url'])
            transcript_response.raise_for_status()
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
                ],
                "created_at": formatted_created_at,
                "language": language
            }
        return {"error": "No transcript available"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {e}"}
    except Exception as e:
        return {"error": f"General error: {e}"}

def fetch_video_description(video_id):
    try:
        url = f'https://www.loom.com/share/{video_id}'
        response = requests.get(url, cookies=cookies, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        description_meta = soup.find('meta', attrs={'name': 'description'})
        return description_meta.get('content', 'No description found.') if description_meta else 'No description found.'
    except requests.exceptions.RequestException as e:
        return f"Request error fetching description: {e}"
    except Exception as e:
        return f"Error fetching description: {e}"

def fetch_video_chapters(video_id):
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'FetchChapters',
        'variables': {'videoId': video_id, 'password': None},
        'query': '''
        query FetchChapters($videoId: ID!, $password: String) {
            fetchVideoChapters(videoId: $videoId, password: $password) {
                ... on VideoChapters {
                    content
                }
                ... on EmptyChaptersPayload {
                    content
                }
            }
        }
        '''
    }
    try:
        response = requests.post(url, cookies=cookies, headers=headers, json=json_data)
        response.raise_for_status()
        response_json = response.json()
        chapters_content = response_json.get('data', {}).get('fetchVideoChapters', {}).get('content', '')
        chapters = []
        if chapters_content:
            chapter_lines = chapters_content.split('\n')
            for line in chapter_lines:
                if line.strip():
                    try:
                        time_step, name = line.split(' ', 1)
                        chapters.append({"name": name, "time_step": time_step})
                    except ValueError:
                        continue
        return chapters
    except requests.exceptions.RequestException as e:
        return f"Request error fetching chapters: {e}"
    except Exception as e:
        return f"Error fetching chapters: {e}"

def fetch_video_details(video_id):
    return {
        "transcript_info": fetch_video_transcript(video_id),
        "summary": fetch_video_description(video_id),
        "chapters": fetch_video_chapters(video_id)
    }

def fetch_videos_from_folder(folder_id, space_id, base_directory):
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'GetLooms',
        'variables': {
            'limit': 10,
            'cursor': None,
            'folderId': folder_id,
            'sourceValue': space_id,
            'source': 'SPACE',
            'sortOrder': 'DESC',
            'sortType': 'RECENT',
        },
        'query': '''
        query GetLooms($limit: Int!, $cursor: String, $folderId: String, $sourceValue: String, $source: LoomsSource!, $sortType: LoomsSortType!, $sortOrder: LoomsSortOrder!) {
            getLooms {
                ... on GetLoomsPayload {
                    videos(first: $limit, after: $cursor, folderId: $folderId, sourceValue: $sourceValue, source: $source, sortType: $sortType, sortOrder: $sortOrder) {
                        edges {
                            cursor
                            node {
                                id
                                name
                            }
                        }
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
        }
        '''
    }
    videos = []
    try:
        while True:
            response = requests.post(url, cookies=cookies, headers=headers, json=json_data)
            response.raise_for_status()
            response_json = response.json()
            videos_data = response_json.get('data', {}).get('getLooms', {}).get('videos', {}).get('edges', [])
            for video in videos_data:
                video_node = video.get('node', {})
                video_id = video_node.get('id')
                video_name = video_node.get('name', 'Unnamed Video')
                if video_id:
                    video_details = fetch_video_details(video_id)
                    videos.append({
                        "video_id": video_id,
                        "video_name": video_name,
                        "details": video_details
                    })
                    # Save each video immediately after fetching its details
                    save_json_to_file({
                        "video_id": video_id,
                        "video_name": video_name,
                        "details": video_details
                    }, base_directory, f"{video_id}.json")
            page_info = response_json.get('data', {}).get('getLooms', {}).get('videos', {}).get('pageInfo', {})
            cursor = page_info.get('endCursor')
            has_next_page = page_info.get('hasNextPage')
            if not has_next_page:
                break
            json_data['variables']['cursor'] = cursor
    except requests.exceptions.RequestException as e:
        print(f"Exception fetching videos: {e}")
    except Exception as e:
        print(f"General error fetching videos: {e}")
    return videos

def fetch_folders(space_id, parent_folder_id=None, base_directory='Loom_Data_Space'):
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'GetPublishedFolders',
        'variables': {
            'first': 10,
            'after': None,
            'source': 'SPACE',
            'sourceValue': space_id,
            'sortOrder': 'DESC',
            'sortType': 'RECENT',
            'parentFolderId': parent_folder_id,
        },
        'query': '''
        query GetPublishedFolders($first: Int!, $after: String, $source: FolderSource!, $sourceValue: String, $sortType: LoomsSortType!, $sortOrder: LoomsSortOrder!, $parentFolderId: String) {
          getPublishedFolders {
            __typename
            ... on GetPublishedFoldersPayload {
              folders(first: $first, after: $after, source: $source, sourceValue: $sourceValue, sortType: $sortType, sortOrder: $sortOrder, parentFolderId: $parentFolderId) {
                edges {
                  cursor
                  node {
                    id
                    name
                    hasSubFolders
                  }
                }
                pageInfo {
                  endCursor
                  hasNextPage
                }
              }
            }
          }
        }
        '''
    }
    folder_structure = {"videos": [], "folders": {}}
    try:
        while True:
            response = requests.post(url, cookies=cookies, headers=headers, json=json_data)
            response.raise_for_status()
            response_json = response.json()
            folders_data = response_json.get('data', {}).get('getPublishedFolders', {}).get('folders', {}).get('edges', [])
            for folder in folders_data:
                folder_node = folder.get('node', {})
                folder_id = folder_node.get('id')
                folder_name = folder_node.get('name', 'Unnamed Folder')
                has_sub_folders = folder_node.get('hasSubFolders', False)
                
                if folder_id:
                    # Create a directory for this folder
                    folder_dir = os.path.join(base_directory, folder_name)
                    if not os.path.exists(folder_dir):
                        os.makedirs(folder_dir)
                    
                    # Fetch videos in the current folder
                    folder_structure["folders"][folder_name] = {
                        "videos": fetch_videos_from_folder(folder_id, space_id, folder_dir),
                        "folders": {}
                    }
                    # Recursively fetch subfolders and their content
                    if has_sub_folders:
                        subfolder_structure = fetch_folders(space_id, folder_id, folder_dir)
                        folder_structure["folders"][folder_name]["folders"] = subfolder_structure["folders"]
                        folder_structure["folders"][folder_name]["videos"].extend(subfolder_structure["videos"])
            page_info = response_json.get('data', {}).get('getPublishedFolders', {}).get('folders', {}).get('pageInfo', {})
            cursor = page_info.get('endCursor')
            has_next_page = page_info.get('hasNextPage')
            if not has_next_page:
                break
            json_data['variables']['after'] = cursor
    except requests.exceptions.RequestException as e:
        print(f"Exception fetching folders: {e}")
    except Exception as e:
        print(f"General error fetching folders: {e}")

    return folder_structure

def get_looms(space_id, base_directory):
    video_details_list = []
    cursor = None

    while True:
        json_data = {
            'operationName': 'GetLooms',
            'variables': {
                'limit': 12,
                'cursor': cursor,
                'folderId': None,
                'sourceValue': space_id,
                'source': 'SPACE',
                'sortOrder': 'DESC',
                'sortType': 'RECENT',
                'filters': [],
                'timeRange': None,
            },
            'query': '''query GetLooms($limit: Int!, $cursor: String, $folderId: String, $sourceValue: String, $source: LoomsSource!, $sortType: LoomsSortType!, $sortOrder: LoomsSortOrder!, $sortGrouping: LoomsSortGrouping, $filters: [[LoomsCollectionFilter!]!], $timeRange: TimeRange) {
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
                        __typename
                      }
                      profileSort
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
            }'''
        }

        try:
            response = requests.post('https://www.loom.com/graphql', cookies=cookies, headers=headers, json=json_data)
            response.raise_for_status()
            response_json = response.json()
            videos = response_json.get('data', {}).get('getLooms', {}).get('videos', {}).get('edges', [])
            for video in videos:
                video_node = video.get('node', {})
                video_id = video_node.get('id')
                video_name = video_node.get('name', 'Unnamed Video')
                if video_id:
                    video_details = fetch_video_details(video_id)
                    video_details_list.append({
                        "video_id": video_id,
                        "video_name": video_name,
                        "details": video_details
                    })
                    # Save each video immediately after fetching its details
                    save_json_to_file({
                        "video_id": video_id,
                        "video_name": video_name,
                        "details": video_details
                    }, base_directory, f"{video_id}.json")

            page_info = response_json.get('data', {}).get('getLooms', {}).get('videos', {}).get('pageInfo', {})
            cursor = page_info.get('endCursor')
            has_next_page = page_info.get('hasNextPage')

            if not has_next_page:
                break
        except requests.exceptions.RequestException as e:
            print(f"Exception fetching looms: {e}")
            break
        except Exception as e:
            print(f"General error fetching looms: {e}")
            break

    return video_details_list

def get_space_memberships():
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'GetMySpaceMemberships',
        'variables': {'first': 20},
        'query': '''
        query GetMySpaceMemberships($first: Int!, $after: String) {
          result: getMySpaceMemberships {
            __typename
            ... on GetMySpaceMembershipsPayload {
              memberships(first: $first, after: $after) {
                edges {
                  node {
                    id
                    space {
                      id
                      name
                    }
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
        response.raise_for_status()
        response_json = response.json()
        memberships = response_json.get('data', {}).get('result', {}).get('memberships', {}).get('edges', [])
        if memberships:
            space_id = memberships[0].get('node', {}).get('space', {}).get('id')
            return space_id
    except requests.exceptions.RequestException as e:
        print(f"Exception: {e}")
    except Exception as e:
        print(f"General error: {e}")
    return None

def save_json_to_file(data, directory, filename):
    """ Save JSON data to a file in the specified directory. """
    if not os.path.exists(directory):
        os.makedirs(directory)  # Create the directory if it doesn't exist

    filepath = os.path.join(directory, filename)
    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def save_folder_structure(folder_structure, base_directory):
    """ Recursively save folder structure and videos to files. """
    # Save videos in the current folder
    if 'videos' in folder_structure:
        for video in folder_structure['videos']:
            video_id = video['video_id']
            video_filename = f"{video_id}.json"
            save_json_to_file(video, base_directory, video_filename)
    
    # Recursively save subfolders
    if 'folders' in folder_structure:
        for folder_name, subfolder_structure in folder_structure['folders'].items():
            subfolder_dir = os.path.join(base_directory, folder_name)
            if not os.path.exists(subfolder_dir):
                os.makedirs(subfolder_dir)
            save_folder_structure(subfolder_structure, subfolder_dir)

def main():
    space_id = get_space_memberships()
    if space_id:
        # Directory for saving JSON files
        base_directory = 'Loom_Data_Space'

        # Fetch videos from the root level using get_looms function
        root_videos = get_looms(space_id, base_directory)
        
        # Fetch folder structure
        folder_structure = fetch_folders(space_id, base_directory=base_directory)
        
        # Add root-level videos to the folder structure
        folder_structure["videos"] = [
            {
                "video_id": video["video_id"],
                "video_name": video["video_name"],
                "details": video["details"]
            }
            for video in root_videos
        ]
        
        # Save folder structure and videos
        save_folder_structure(folder_structure, base_directory)
        
        print(f"Data saved successfully in {base_directory}")
    else:
        print("No space ID found.")

if __name__ == "__main__":
    main()

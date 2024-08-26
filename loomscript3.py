import requests
import json
import sys


# Enable or disable debug mode
DEBUG = True
# Define cookies and headers
cookies = {
    'loom_anon_comment': '163a60c1706f44899d700c43d05f2511',
    'ajs_anonymous_id': '%22d927c6be-5331-4489-9d2c-446878991348%22',
    'ajs_anonymous_id': 'd927c6be-5331-4489-9d2c-446878991348',
    'loom_referral_video': '17a2cab1cd8d4c28bbb81a37db2119e8',
    'mutiny.user.token': 'ecf333a3-4171-4798-b398-2506377fa865',
    'mutiny.user.session': '498ea70f-2709-4a87-9e73-32d0d21dd7a7',
    'mutiny.user.session_number': '1',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Mon+Aug+26+2024+14%3A47%3A04+GMT%2B0500+(Pakistan+Standard+Time)&version=202407.1.0&browserGpcFlag=1&isIABGlobal=false&identifierType=null&hosts=&landingPath=https%3A%2F%2Fwww.loom.com%2Fsignup&groups=1%3A1%2C2%3A1%2C3%3A1%2C4%3A1',
    '_ga': 'GA1.1.1063612768.1724665627',
    '_rdt_uuid': '1724665627520.e2874f28-0eff-49c2-8fe0-ce8f254d53da',
    'loom_anon_id': 'd927c6be-5331-4489-9d2c-446878991348',
    'loom_app_source': 'website',
    'loom-sst-supported': 'true',
    '_uetsid': '28f51680639011efa20cf1bbf44e90e7',
    '_uetvid': '28f52700639011efa03411d994ac314a',
    '_fbp': 'fb.1.1724665632578.492852347291801677',
    '__hstc': '185935670.aef9f528e8c85e9072d4f2aca9cef488.1724665632626.1724665632626.1724665632626.1',
    'hubspotutk': 'aef9f528e8c85e9072d4f2aca9cef488',
    '_ttp': 'Ohht_LTubqUdoPCv-VRjd6wz1zQ',
    'connect.sid': 's%3AhT1UYCxLi2IpOqHOneNNGozXaYPyistf.Ksl%2FaDzsVwPtOw3xgcpIkYvQi%2BqedlYhrQgWNN7%2FG90',
    'loom-sst': 'lsst-0389a6bc-5ae3-45c5-9e07-568a3a821324',
    '_ga_H93TGDH6MB': 'GS1.1.1724665627.1.0.1724665654.33.0.0',
    'ajs_user_id': '32220198',
    '__stripe_mid': 'cb39c45f-7ef7-4889-8064-e7ec38de53891e0f86',
    '__stripe_sid': '8a44336f-4794-4e21-887a-19c73d03d3b13cda4d',
    '__Host-psifi.analyticsTrace': 'e91f7c17fca569c6c51564985c6e7b8a7be70e81b105e3e707254b1a1d3e59c3',
    '__Host-psifi.analyticsTraceV2': '9206043ca0e3b956ac09a64b37bd17592d108b71b13f3d7d4bba46200fa9f1309b891b8ce6a7c167b003f00fcc75638d4e9246abf4e32114fe35d57faee1e96a',
    'AWSALBAuthNonce': '1upDd6jNyMu1PFVF',
    '_dd_s': 'rum=0&expire=1724666711348&logs=1&id=2582e116-c2f6-44c3-8d28-9aeff1529849&created=1724665619090',
}

headers = {
    'accept': '*/*',
    'accept-language': 'en-PK,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,it;q=0.6',
    'apollographql-client-name': 'web',
    'apollographql-client-version': '2564a2c',
    'content-type': 'application/json',
    'origin': 'https://www.loom.com',
    'priority': 'u=1, i',
    'referer': 'https://www.loom.com/looms/videos',
    'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'x-loom-request-source': 'loom_web_2564a2c',
}



def debug_print(message):
    if DEBUG:
        print(message)

# Function to fetch video transcripts
def fetch_video_transcript(video_id, folder_path):
    url = 'https://www.loom.com/graphql'
    json_data = {
        'operationName': 'FetchVideoTranscript',
        'variables': {
            'videoId': video_id,
            'password': None,
        },
        'query': '''
        query FetchVideoTranscript($videoId: ID!, $password: String) {
            fetchVideoTranscript(videoId: $videoId, password: $password) {
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
        debug_print(f"[fetch_video_transcript] Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"Failed to fetch transcript for Video ID: {video_id}. HTTP Status Code: {response.status_code}")
            return

        response_json = response.json()
        debug_print(f"[fetch_video_transcript] Response JSON: {json.dumps(response_json, indent=2)}")

        transcript_data = response_json.get('data', {}).get('fetchVideoTranscript', {})

        if transcript_data.get('__typename') == 'VideoTranscriptDetails':
            source_url = transcript_data.get('source_url')
            if source_url:
                transcript_response = requests.get(source_url)
                if transcript_response.status_code == 200:
                    transcript_json = transcript_response.json()
                    phrases = transcript_json.get('phrases', [])
                    paragraph = " ".join([phrase.get('value', '') for phrase in phrases])

                    print(f"\nTranscript for video '{video_id}' in folder '{folder_path}':\n")
                    print(paragraph)
                    print("\nLink:")
                    print(source_url)
                    print("\n" + "=" * 80 + "\n")
                else:
                    print(f"Failed to retrieve transcript text for Video ID: {video_id}. HTTP Status Code: {transcript_response.status_code}")
            else:
                print(f"No transcript available for Video ID: {video_id}")
        elif transcript_data.get('__typename') == 'GenericError':
            error_message = transcript_data.get('message', 'Unknown error')
            print(f"Error fetching transcript for Video ID: {video_id}: {error_message}")
        else:
            print(f"Unexpected response structure when fetching transcript for Video ID: {video_id}")
    except Exception as e:
        print(f"Exception occurred while fetching transcript for Video ID: {video_id}: {e}")

# Function to fetch videos from a folder
def fetch_videos_from_folder(folder_id=None, folder_path=""):
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
            'filters': [],
            'timeRange': None,
        },
        'query': '''
        query GetLooms($limit: Int!, $cursor: String, $folderId: String, $source: LoomsSource!, $sortType: LoomsSortType!, $sortOrder: LoomsSortOrder!, $filters: [[LoomsCollectionFilter!]!], $timeRange: TimeRange) {
            getLooms {
                ... on GetLoomsPayload {
                    videos(
                        first: $limit
                        after: $cursor
                        folderId: $folderId
                        source: $source
                        sortType: $sortType
                        sortOrder: $sortOrder
                        filters: $filters
                        timeRange: $timeRange
                    ) {
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
        debug_print(f"[fetch_videos_from_folder] Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"Failed to fetch videos for Folder ID: {folder_id}. HTTP Status Code: {response.status_code}")
            return

        response_json = response.json()
        debug_print(f"[fetch_videos_from_folder] Response JSON: {json.dumps(response_json, indent=2)}")

        videos_data = response_json.get('data', {}).get('getLooms', {}).get('videos', {}).get('edges', [])

        if not videos_data:
            print(f"No videos found in folder '{folder_path}' (Folder ID: {folder_id})")
            return

        for video in videos_data:
            video_node = video.get('node', {})
            video_id = video_node.get('id')
            video_name = video_node.get('name', 'Unnamed Video')

            if video_id:
                safe_video_name = video_name.encode('utf-8', 'replace').decode('utf-8')
                print(f"Fetching transcript for video: '{safe_video_name}' (ID: {video_id}) in folder '{folder_path}'")
                fetch_video_transcript(video_id, folder_path)
            else:
                print(f"Invalid video data encountered in folder '{folder_path}': {video_node}")
    except Exception as e:
        print(f"Exception occurred while fetching videos for Folder ID: {folder_id}: {e}")

# Function to recursively fetch all folders and their contents
def fetch_folders(parent_folder_id=None, folder_path=""):
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
            'filters': [],
            'timeRange': None,
        },
        'query': '''
        query GetPublishedFolders($first: Int!, $after: String, $source: FolderSource!, $sortType: LoomsSortType!, $sortOrder: LoomsSortOrder!, $parentFolderId: String, $filters: [LoomsCollectionFilter!], $timeRange: TimeRange) {
            getPublishedFolders {
                ... on GetPublishedFoldersPayload {
                    folders(
                        first: $first
                        after: $after
                        source: $source
                        sortType: $sortType
                        sortOrder: $sortOrder
                        parentFolderId: $parentFolderId
                        filters: $filters
                        timeRange: $timeRange
                    ) {
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
        debug_print(f"[fetch_folders] Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"Failed to fetch folders under Parent Folder ID: {parent_folder_id}. HTTP Status Code: {response.status_code}")
            return

        response_json = response.json()
        debug_print(f"[fetch_folders] Response JSON: {json.dumps(response_json, indent=2)}")

        folders_data = response_json.get('data', {}).get('getPublishedFolders', {}).get('folders', {}).get('edges', [])

        if not folders_data:
            print(f"No subfolders found under folder '{folder_path}' (Parent Folder ID: {parent_folder_id})")
            return

        for folder in folders_data:
            folder_node = folder.get('node', {})
            folder_id = folder_node.get('id')
            folder_name = folder_node.get('name', 'Unnamed Folder')
            has_sub_folders = folder_node.get('hasSubFolders', False)

            if folder_id:
                new_folder_path = f"{folder_path}/{folder_name}".strip('/')
                print(f"\nEntering folder: '{new_folder_path}' (ID: {folder_id})")
                fetch_videos_from_folder(folder_id, new_folder_path)

                if has_sub_folders:
                    fetch_folders(folder_id, new_folder_path)
            else:
                print(f"Invalid folder data encountered: {folder_node}")
    except Exception as e:
        print(f"Exception occurred while fetching folders under Parent Folder ID: {parent_folder_id}: {e}")

if __name__ == "__main__":
    print("Starting processing of Loom videos and folders...\n")

    # Process videos in the main/root folder
    print("Processing videos in the root folder...\n")
    fetch_videos_from_folder(folder_id=None, folder_path="Root")

    # Process all folders and their nested contents
    print("\nProcessing subfolders...\n")
    fetch_folders(parent_folder_id=None, folder_path="Root")

    print("\nFinished processing all folders and videos.")

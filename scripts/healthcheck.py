import requests
import sys

def check_endpoint(url, validate_json=False):

    try:

        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            print(f"FAILED - {url} responded with {response.status_code}")
            return False

        if validate_json:
            data = response.json()
            if not isinstance(data, list):
                print(f"FAILED - {url} did not return a list as expected")
                return False
            print(f"OK - {url} responded with 200, {len(data)} item(s)")
        else:
            print(f"OK - {url} responded with 200")

        return True

    except requests.exceptions.RequestException as e:
        print(f"FAILED - {url} unreachable: {e}")
        return False

    except ValueError:
        print(f"FAILED - {url} did not return valid JSON")
        return False

def main():

    base_url = "http://localhost:8080"
    checks = [
        (f"{base_url}/", False),
        (f"{base_url}/pods", True),
        (f"{base_url}/nodes", True),
    ]

    results = [check_endpoint(url, validate_json) for url, validate_json in checks]

    if all(results):
        print("All checks passed")
        sys.exit(0)
    else:
        print("One or more checks failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
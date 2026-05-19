import json

def write_clean_log(path, message):
    data = {"message": message}
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data) + '\n')

if __name__ == "__main__":
    path = "soar/velociraptor/velociraptor/events.json"
    write_clean_log(path, "VELOCIRAPTOR_FINAL_PROFESSIONAL_SUCCESS")
    print(f"Clean log written to {path}")

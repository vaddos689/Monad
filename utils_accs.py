def read_file_data(file_path):
    with open(file_path, 'r') as file:
        return [r.strip() for r in file]

def get_accounts():
    private_keys_file_path = 'import/private_keys.txt'
    proxies_file_path = 'import/proxies.txt'
    private_keys = read_file_data(private_keys_file_path)
    proxies = read_file_data(proxies_file_path)

    accounts = []
    for i in range(len(private_keys)):
        account = {
            'id': i + 1,
            'private_key': private_keys[i],
            'proxy': proxies[i]
        }
        accounts.append(account)
    
    return accounts

def write_result(text):
    with open('result.txt', 'a') as file:
        file.write(text)
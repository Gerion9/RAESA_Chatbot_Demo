import streamlit_authenticator as stauth

# Generate hashes
passwords = ['admin123', 'user123']
hashes = stauth.Hasher(passwords).generate()

print("\nGenerated hashes:")
for password, hash in zip(passwords, hashes):
    print(f"\nPassword: {password}")
    print(f"Hash: {hash}") 
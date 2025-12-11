from dotenv import load_dotenv
import os

print("=== Testing .env file loading ===\n")

# Check before loading
key_before = os.getenv("OPENAI_API_KEY")
print(f"Before load_dotenv(): {'SET' if key_before else 'NOT SET'}")

# Load .env file
load_dotenv(override=True)

# Check after loading
key_after = os.getenv("OPENAI_API_KEY")

if key_after:
    print(f"\n✅ Key loaded from .env")
    print(f"   Length: {len(key_after)}")
    print(f"   First 10 chars: {key_after[:10]}")
    print(f"   Last 10 chars: {key_after[-10:]}")
    
    # Check for common issues
    issues = []
    if key_after.startswith(' '):
        issues.append("⚠️ Has leading space")
    if key_after.endswith(' '):
        issues.append("⚠️ Has trailing space")
    if key_after.startswith('"') or key_after.startswith("'"):
        issues.append("⚠️ Has quotes")
    if not key_after.startswith('sk-'):
        issues.append("⚠️ Doesn't start with 'sk-'")
    if len(key_after) < 20:
        issues.append("⚠️ Key seems too short")
    
    if issues:
        print("\n⚠️ Issues found:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ Key format looks good!")
        
    # Show the actual key (be careful with this!)
    print(f"\n🔑 Full key (for verification):")
    print(f"   {key_after}")
else:
    print("\n❌ No key found in .env file")
    print("   Make sure your .env file has:")
    print("   OPENAI_API_KEY=sk-...")
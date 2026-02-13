import asyncio
import os
os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")

from ai_router import ai_router

async def verify_tweet():
    # Simulating the tweet from @tech_nurgaliyev
    tweet_text = """Shipfast alternative in Python

I'm thinking to build an alternative to Shipfast (NextJS) in Python (FastAPI + React + Tailwind)

Pros:
- easier to understand backend
- still fast
- Python is #1 language

What do you think?"""
    
    username = "tech_nurgaliyev"
    
    # Quick filters first
    if tweet_text.startswith("RT @"):
        print("❌ FILTERED: Retweet")
        return
    if tweet_text.startswith("@"):
        print("❌ FILTERED: Reply")
        return
    if len(tweet_text) < 50:
        print("❌ FILTERED: Too short")
        return
    
    # AI verification using GPT-5-nano (our new model)
    prompt = f"""Analyze this tweet for VALUE to builders/founders.

Tweet: "{tweet_text}"
Username: @{username}

Check:
- Original insight? Tutorial/playbook? Case study? Tool recommendation?
- Signal vs noise for startup builders
- Would a founder learn/build something useful?

Return JSON:
{{
  "should_send": true/false,
  "reason": "brief explanation",
  "category": "insight|tutorial|tool|playbook|case_study|other",
  "score": 1-10
}}"""

    print("="*60)
    print(f"📝 Tweet by @{username}")
    print(f"📄 Content: {tweet_text[:100]}...")
    print("="*60)
    print("\n🤖 Sending to GPT-5-nano for verification...\n")
    
    try:
        response = await ai_router.generate(
            prompt=prompt,
            task_type="analysis",
            temperature=0.3,
            max_tokens=500
        )
        
        print("✅ AI Response:")
        print("-"*60)
        print(response)
        print("-"*60)
        
        # Try to parse JSON
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            print(f"\n📊 RESULT:")
            print(f"   Should send to Discord: {'✅ YES' if data.get('should_send') else '❌ NO'}")
            print(f"   Category: {data.get('category', 'N/A')}")
            print(f"   Score: {data.get('score', 'N/A')}/10")
            print(f"   Reason: {data.get('reason', 'N/A')}")
            
            # Our routing logic
            score = data.get('score', 0)
            if score >= 8:
                print(f"\n🎯 ROUTING: Telegram (score {score} >= 8)")
            elif score >= 5:
                print(f"\n📱 ROUTING: Discord (score {score} between 5-7)")
            else:
                print(f"\n🗑️ ROUTING: Filtered (score {score} < 5)")
        else:
            print("⚠️ Could not parse JSON response")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_tweet())

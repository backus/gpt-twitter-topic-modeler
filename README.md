# GPT Twitter Topic Modeler

Scrape the tweets from a user (excluding retweets and replies) and then generate a topic model for them based on the tweets.

## Example:

```sh
$ python twitter_topic_model.py --username backus
{
  "AI Tools": {
    "Copilot in terminal": ["excited"],
    "SQL-like abstraction on top of Gmail": ["curious"],
    "Static site generator": ["interested"],
    "HTTP client for JSON API": ["analytical"],
    "Automated software security scanner": ["annoyed"]
  },
  "Miami": {
    "Weather": ["positive"],
    "Tech hub potential": ["optimistic"],
    "Accessibility": ["positive"],
    "Network effects": ["mixed"],
    "City governance": ["negative"]
  },
  "Decentralization": {
    "Legal boundaries": ["optimistic"],
    "Crypto's future": ["pessimistic"],
    "Pushback": ["clarifying"],
    "Adoption timeline": ["mismatched"],
    "Legal culling": ["hopeful"],
    "Minimum viable decentralization": ["skeptical"],
    "P2P file sharing": ["informative"],
    "Crypto tokens": ["difficult"],
    "Search for BitTorrent": ["curious"],
    "Waves of decentralization": ["historical"]
  },
  "History": {
    "LSD's dark history in the US": ["critical"],
    "CIA's research on LSD": ["critical"],
    "US history that sounds fake": ["informative"],
    "Government control": ["critical"],
    "Breakthrough therapeutic tools": ["hopeful"]
  }
}
```

Note: this is a truncated version ^. My real output is 35 topics with 190 subtopics.

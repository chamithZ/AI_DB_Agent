# main.py
from agent import DBAgent

if __name__ == "__main__":
    agent = DBAgent()

    user_input = "Find all users  ."
    response = agent.query_database(user_input)

    print("Query Result:", response)

    agent.close()

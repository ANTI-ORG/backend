from sqlalchemy.exc import SQLAlchemyError
from app.models import Base, User, IpAddress, Quest, Chain, Project, Wallet, WalletNetwork, Task  # Замените на актуальные пути
from app.database import get_db, engine

def create_fixtures():
    session = get_db().__next__()

    try:
        # Создаем все таблицы, если они еще не существуют
        Base.metadata.create_all(engine)

        # Добавляем данные в таблицу Chain
        if not session.query(Chain).first():
            chains = [
                Chain(name="Chain 1"),
                Chain(name="Chain 2"),
                Chain(name="Chain 3")
            ]
            session.bulk_save_objects(chains)
            session.commit()

        # Добавляем данные в таблицу Project
        if not session.query(Project).first():
            projects = [
                Project(name="Project 1"),
                Project(name="Project 2"),
                Project(name="Project 3")
            ]
            session.bulk_save_objects(projects)
            session.commit()

        # Добавляем данные в таблицу IpAddress
        if not session.query(IpAddress).first():
            ip_addresses = [
                IpAddress(ip="192.168.1.1"),
                IpAddress(ip="192.168.1.2"),
                IpAddress(ip="192.168.1.3")
            ]
            session.bulk_save_objects(ip_addresses)
            session.commit()

        # Добавляем данные в таблицу User
        if not session.query(User).first():
            users = [
                User(username="user1", xp=100),
                User(username="user2", xp=200),
                User(username="user3", xp=300)
            ]
            session.bulk_save_objects(users)
            session.commit()

        # Проверяем, что в базе есть 3 записи в таблице User
        user_count = session.query(User).count()
        if user_count == 3:
            # Получаем UUID пользователей после их создания
            user_mapping = {user.username: user.id for user in session.query(User).all()}

            # Добавляем данные в таблицу Wallet
            if not session.query(Wallet).first():
                wallets = [
                    Wallet(
                        web3_address="0x97895",
                        wallet_network=WalletNetwork.Ethereum,
                        user_id=user_mapping["user1"]
                    ),
                    Wallet(
                        web3_address="0x67890",
                        wallet_network=WalletNetwork.Ethereum,
                        user_id=user_mapping["user2"]
                    ),
                    Wallet(
                        web3_address="0xabcde",
                        wallet_network=WalletNetwork.Solana,
                        user_id=user_mapping["user3"]
                    )
                ]
                session.bulk_save_objects(wallets)
                session.commit()
        else:
            print(f"Error: Expected 3 users, found {user_count}.")

        # Добавляем данные в таблицу Quest
        if not session.query(Quest).first():
            quests = [
                Quest(
                    title="Quest 1",
                    description="Description for quest 1",
                    xp=50,
                    chain_id=1,
                    project_id=1
                ),
                Quest(
                    title="Quest 2",
                    description="Description for quest 2",
                    xp=100,
                    chain_id=2,
                    project_id=2
                ),
                Quest(
                    title="Quest 3",
                    description="Description for quest 3",
                    xp=150,
                    chain_id=3,
                    project_id=3
                )
            ]
            session.bulk_save_objects(quests)
            session.commit()

            # Добавляем данные в таблицу Task для каждого квеста
            tasks = [
                Task(
                    title="Task 1 for Quest 1",
                    description="Description for task 1",
                    button_text="Start",
                    button_link="https://www.google.com/",
                    quest_id=1
                ),
                Task(
                    title="Task 2 for Quest 1",
                    description="Description for task 2",
                    button_text="Proceed",
                    button_link="https://www.google.com/",
                    quest_id=1
                ),
                Task(
                    title="Task 1 for Quest 2",
                    description="Description for task 1",
                    button_text="Start",
                    button_link="https://www.google.com/",
                    quest_id=2
                ),
                Task(
                    title="Task 2 for Quest 2",
                    description="Description for task 2",
                    button_text="Continue",
                    button_link="https://www.google.com/",
                    quest_id=2
                ),
                Task(
                    title="Task 1 for Quest 3",
                    description="Description for task 1",
                    button_text="Go",
                    button_link="https://www.google.com/",
                    quest_id=3
                ),
                Task(
                    title="Task 2 for Quest 3",
                    description="Description for task 2",
                    button_text="Next",
                    button_link="https://www.google.com/",
                    quest_id=3
                )
            ]
            session.bulk_save_objects(tasks)
            session.commit()

    except SQLAlchemyError as e:
        session.rollback()
        print(f"An error occurred: {e}")

    finally:
        session.close()


if __name__ == "__main__":
    create_fixtures()

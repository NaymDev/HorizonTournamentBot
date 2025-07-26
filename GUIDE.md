# Guide (How to)
## Guide for the guide
When reading the commands below, you'll see parts wrapped in angle brackets like this: <example>. Here's what they mean:
- <something> → Required
You must include this part(argument) when using the command.

- <(something)> → Optional
This part(argument) is optional. You can include it if you want, but it's not required.

## Commands
### For Users
- `/hello`

    On the outside it just greets the user. But this command __has to be executed__ at least once before a member can register their Minecraft account.

- `/register <ign>`

    This command can be used to link your Minecraft account. It will check the Discord social linked on hypixel for the given Minecraft account

- `/signup <name> <p1> <p2> <p3>`

    This command will signup a team including yourself with the given name `<name>` and team members `<p1> <p2> <p3>`. It has to be executed in the signup channel for the correct tournament.

### For Staff
- `/ping`
    
    This command will display the bots current ping as well as a ghraph showing the ping over time.

- `/create_tournament <name> <start_date> <signup_channel> <(max_accepted_teams)>`
    
    This command is used to create a tournament. It will setup a tournament on challonge and will enable signups in the specified channel. The `start_date` parameter currently has no functionality

- `/start_tournament <tournament>`

    This command will close signups for the given tournament!

- `/register_other <discord_member> <ign>`

    Allows an authorized member to register a Minecraft account for someone else. This still requires a valid Minecraft account =>
    - Minecraft account exists
    - The linked Discord social on hypixel matches the `<discord_member>`
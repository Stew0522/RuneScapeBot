from random import choice
from datetime import datetime as dt, timedelta
from asyncio import sleep
from cogs.utils.custom_embed import CustomEmbed
from cogs.utils.provably_fair import ProvablyFair
from cogs.utils.currency_validator import NewScape
from cogs.utils.money_fetcher import money_displayer


RED = 0xFF0000
GREEN = 0x00FF00


class Giveaway(object):

    def __init__(self, bot):
        self.bot = bot

        # Store the config from the JSON for easy use
        self.config = bot.config['Giveaway']
        self.channel_id = self.config['channel']
        self.timeout = self.config['timeout']
        self.duration = self.config['duration']
        self.amount = self.config['giveaway']

        # See if the giveaway is currently counting users
        self.running = False
        self.counted = set()

        # See when the giveaway was last run
        self.lastrun = dt.now()
        # self.lastrun = dt(year=2000, month=1, day=1)


    async def auto_giveaway(self):
        '''
        Runs the giveaway code for the bot
        '''

        # Get stuff ready
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.channel_id)
        remaining_time = lambda x: 'Giveaway of **{} RS3**! Type a message within the next {} seconds to be entered!'.format(money_displayer(self.amount), x)

        # Loop until the bot is closed
        while not self.bot.is_closed():
            if dt.now() >= self.lastrun + timedelta(minutes=self.timeout):

                # Tell the users about it
                with CustomEmbed() as e:
                    e.description = remaining_time(self.duration)
                    e.colour = GREEN
                message = await channel.send(embed=e)
                self.running = True 
                self.lastrun = dt.now()

                # Wait for messages to roll in
                current_users = 0
                running_duration = 0
                edited = False
                duration_editor = 5  # Change the embed every x seconds

                while dt.now() < self.lastrun + timedelta(seconds=self.duration):

                    working_running_duration = (dt.now() - (self.lastrun + timedelta(seconds=self.duration))).total_seconds()
                    working_running_duration = int(running_duration / duration_editor)
                    if working_running_duration > running_duration:
                        running_duration = working_running_duration
                        e.description = remaining_time(self.duration - (working_running_duration * duration_editor))
                        edited = True

                    if len(self.counted) > current_users:
                        current_users = len(self.counted)
                        try:
                            e.set_field_at(0, name='Entered Users', value=current_users)
                        except Exception:
                            e.add_new_field('Entered Users', current_users)
                        edited = True
                    await message.edit(embed=e)
                    await sleep(1)

                self.running = False

                # Generate a random number
                users = list(self.counted)

                # Check that *someone* entered
                if users:

                    chosen_user = choice(users)
                    async with self.bot.database() as db:
                        await db.modify_user_currency(chosen_user, self.amount, NewScape())
                        await db.log_user_mod(
                            message=message, 
                            to=chosen_user, 
                            amount=self.amount, 
                            currency=NewScape(), 
                            reason='GIVEAWAY'
                            )
                    self.counted = set()

                    # Tell them about it
                    with e as e:
                        e.description = 'Giveaway over!'
                        e.colour = RED
                    await message.edit(embed=e)
                    await channel.send('<@{}> you just won **{} RS3**!'.format(chosen_user, money_displayer(self.amount)))

                else:

                    # Nobody entered
                    await message.edit(content='Guess nobody wants any free money then :/')

            await sleep(60)

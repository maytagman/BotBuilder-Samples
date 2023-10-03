import os
import json
import requests
from botbuilder.core import ActivityHandler, TurnContext, CardFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes

class AdaptiveCardsBot(ActivityHandler):
    def __init__(self):
        self.default_units = "metric"  # Default celsius
        self.units_toggle = False  # False for celsius, true for fahrenheit

    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    f"Welcome to the Open Weather Adaptive Cards Bot, {member.name}. "
                    f"Type 'weather' followed by a city name to see weather information. "
                    f"You can also type 'toggle units' to switch between Celsius and Fahrenheit."
                )

    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.text.lower() == "weather":
            await turn_context.send_activity("Please provide a city name after 'weather' to get weather information.")

        elif turn_context.activity.text.lower().startswith("weather"):
            city = turn_context.activity.text[7:].strip().capitalize()  # Extract the city name after "weather" and capitalize it

            if city:
                weather_card = await self._get_weather_adaptive_card(city)
                message_activity = Activity(
                    text="Here is the weather information:",
                    type=ActivityTypes.message,
                    attachments=[weather_card]
                )
                await turn_context.send_activity(message_activity)
            else:
                await turn_context.send_activity("Please provide a city name after 'weather' to get weather information.")

        elif turn_context.activity.text.lower() == "toggle units":
            self.units_toggle = not self.units_toggle
            units_message = "Celsius" if not self.units_toggle else "Fahrenheit"
            await turn_context.send_activity(f"Temperature units toggled to {units_message}.")

    async def _get_weather_adaptive_card(self, city):
        units = "imperial" if self.units_toggle else self.default_units  # Toggle units based on user choice
        api_key = "xyz"  # Replace with your openweathermap api key
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": units
        }

        response = requests.get(base_url, params=params)
        data = response.json()

        if data.get("cod") == 200:
            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            icon = data["weather"][0]["icon"]
            
            # url for the weather icon
            icon_url = f"http://openweathermap.org/img/w/{icon}.png"
            
            # Adaptive card to show weather information, moved json to main bot code to speed up troubleshooting with formatting the adaptive card, would move back to a separate json file as soon as more adaptive cards were added to the bot
            card_data = {
                "type": "AdaptiveCard",
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "version": "1.3",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": f"Weather in {city}",
                        "wrap": True,
                        "size": "Large",
                        "weight": "Bolder"
                    },
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [
                                    {
                                        "type": "Image",
                                        "url": icon_url,
                                        "size": "small"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"Humidity: {humidity}%",
                                        "wrap": True
                                    }
                                ]
                            },
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": f"{temperature}°{'F' if self.units_toggle else 'C'}",
                                        "size": "ExtraLarge",
                                        "weight": "Bolder",
                                        "height": "stretch",
                                        "horizontalAlignment": "Left",
                                        "spacing": "Medium",
                                        "wrap": True
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"Description: {description}",
                                        "wrap": True
                                    }
                                ],
                                "backgroundImage": {
                                    "verticalAlignment": "Center"
                                }
                            }
                        ]
                    }
                ]
            }

            return CardFactory.adaptive_card(card_data)
        else:
            # Create an adaptive card for the error message
            error_card_data = {
                "type": "AdaptiveCard",
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "version": "1.3",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": f"Sorry, I couldn't retrieve weather information for {city}.",
                        "wrap": True
                    }
                ]
            }

            return CardFactory.adaptive_card(error_card_data)

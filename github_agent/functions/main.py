from google.adk.runners import Runner
from google.adk.events import Event
from google.genai import types


from google.adk.runners import Runner
from google.adk.events import Event
from google.genai import types


async def process_event(event: Event):
    # Handle None content
    if event.content is None:
        return None

    # Handle final response
    if event.is_final_response():
        if event.content.parts and len(event.content.parts) > 0:
            # Check if it's text content
            if hasattr(event.content.parts[0], 'text') and event.content.parts[0].text:
                output = event.content.parts[0].text.strip()
                return output
            
            #TODO: Need to check if it is needed or not
            # elif hasattr(event.content.parts[0], 'function_response') and event.content.parts[0].function_response:
            #     output = event.content.parts[0].function_response.model_dump(mode="python")
            #     print("Final Response:", output)
            #     return output
        return None
    return None


async def call_agent(runner: Runner, user_id: str, session_id: str, query: str):
    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response = None

    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            resp = await process_event(event)
            if resp:
                final_response = resp

        # if final_response is None:
        #     final_response = "No response from agent"

    except Exception as e:
        print(f"Error during agent execution: {e}")
        final_response = f"Error: {str(e)}"

    return final_response

import asyncio
import logging
import os
import textwrap
from typing import List, Dict, Any
from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Code Snippet MCP Server")

# Dictionary of sample data for different types of code snippets
SAMPLE_DATA = [
    {
        "type": "sql",
        "snippet": textwrap.dedent("""
            SELECT
                o.order_id,
                o.order_date,
                c.customer_name,
                p.product_name,
                oi.quantity,
                oi.price_per_unit
            FROM
                orders AS o
            JOIN
                customers AS c ON o.customer_id = c.customer_id
            JOIN
                order_items AS oi ON o.order_id = oi.order_id
            JOIN
                products AS p ON oi.product_id = p.product_id
            WHERE
                o.order_date >= '2024-01-01'
            ORDER BY
                o.order_date DESC, c.customer_name ASC;
        """)
    },
    {
        "type": "python",
        "snippet": textwrap.dedent("""
            def find_even_numbers(numbers_list):
                '''
                Finds and returns all even numbers from a list of integers.

                Args:
                    numbers_list (list): A list of integers.

                Returns:
                    list: A new list containing only the even numbers from the input list.
                '''
                # A list comprehension is a concise way to create lists.
                # The expression iterates through each number in the input list
                # and includes it in the new list only if the condition (number % 2 == 0) is true.
                return [number for number in numbers_list if number % 2 == 0]

            # --- Example Usage ---
            my_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            even_numbers = find_even_numbers(my_numbers)

            print(f"Original list: {my_numbers}")
            print(f"Even numbers found: {even_numbers}")

            # --- Output ---
            # Original list: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            # Even numbers found: [2, 4, 6, 8, 10, 12]
        """)
    },
    {
        "type": "javascript",
        "snippet": textwrap.dedent("""
            // A reference to the HTML element where we will display the user data.
            const userContainer = document.getElementById('user-container');

            /**
            * Fetches random user data from the Random User Generator API.
            * This is an 'async' function, which allows us to use 'await'.
            */
            async function getRandomUser() {
                try {
                    // Use 'fetch' to make a network request to the API.
                    // 'await' pauses the function until the request is complete.
                    const response = await fetch('https://randomuser.me/api/');

                    // Check if the network response was successful.
                    if (!response.ok) {
                        throw new Error(`Network response was not ok: ${response.statusText}`);
                    }

                    // Parse the JSON data from the response.
                    // 'await' pauses the function until the JSON is fully parsed.
                    const data = await response.json();
                    
                    // The API returns results in an array, so we get the first user.
                    const user = data.results[0];

                    // Call the function to display the user data on the page.
                    displayUser(user);

                } catch (error) {
                    // If anything goes wrong (network error, parsing error, etc.),
                    // we catch the error here and display a message.
                    console.error('Error fetching user data:', error);
                    userContainer.innerHTML = '<p>Sorry, could not fetch a user. Please try again later.</p>';
                }
            }

            /**
            * Renders the user data into the userContainer element.
            * @param {object} user - The user object from the API.
            */
            function displayUser(user) {
                const userHTML = `
                    <img src="${user.picture.large}" alt="User picture">
                    <h2>${user.name.first} ${user.name.last}</h2>
                    <p>Email: ${user.email}</p>
                    <p>Location: ${user.location.city}, ${user.location.country}</p>
                `;
                
                // Replace the "Loading..." message with the new HTML.
                userContainer.innerHTML = userHTML;
            }

            // Call the function to fetch a user when the script loads.
            getRandomUser();
        """)
    },
    {
        "type": "json",
        "snippet": textwrap.dedent("""
            {
                "squadName": "Super hero squad",
                "homeTown": "Metro City",
                "formed": 2016,
                "secretBase": "Super tower",
                "active": true,
                "members": [
                    {
                        "name": "Molecule Man",
                        "age": 29,
                        "secretIdentity": "Dan Jukes",
                        "powers": [
                            "Radiation resistance",
                            "Turning tiny",
                            "Radiation blast"
                        ]
                    },
                    {
                        "name": "Madame Uppercut",
                        "age": 39,
                        "secretIdentity": "Jane Wilson",
                        "powers": [
                            "Million tonne punch",
                            "Damage resistance",
                            "Superhuman reflexes"
                        ]
                    }
                ]
            }
        """)
    },
    {
        "type": "go",
        "snippet": textwrap.dedent("""
            package main
            import "fmt"

            // findEvenNumbers returns a slice containing even numbers from input.
            func findEvenNumbers(numbers []int) []int {
                result := []int{}
                for _, n := range numbers {
                    if n%2 == 0 {
                        result = append(result, n)
                    }
                }
                return result
            }

            func main() {
                nums := []int{1,2,3,4,5,6,7,8,9,10,11,12}
                evens := findEvenNumbers(nums)
                fmt.Printf("Original: %v\nEven: %v\n", nums, evens)
            }
        """)
    }
]

@mcp.tool()
def get_code_snippet(type: str) -> str:
    """
    Retrieves sample code snippets by type formatted as markdown.

    Args:
        type: The type of code snippet to retrieve (sql, python, javascript, json, or go).

    Returns:
        A markdown-formatted string containing the code snippet with proper syntax highlighting.
        Returns an error message if the type is not found.
    """
    logger.info(f">>> 🛠️ Tool: 'get_code_snippet' called for '{type}'")

    matching_samples = [s for s in SAMPLE_DATA if s["type"].lower() == type.lower()]

    if not matching_samples:
        available_types = ", ".join(sorted({s["type"] for s in SAMPLE_DATA}))
        return f"No sample data found for type: {type}. Available types: {available_types}"

    sample = matching_samples[0]
    code_type = sample["type"]
    code_snippet = sample["snippet"].strip()

    return f"```{code_type}\n{code_snippet}\n```"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 MCP server started on port {port}")
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=port,
        )
    )
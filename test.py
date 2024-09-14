import requests
import sys
import matplotlib.pyplot as plt

def test_country_image_request(country_name):
    url = f"https://www.mydraw.com/NIMG.axd?i=Shape-Libraries/Maps/Country-Shapes/{country_name}.png"
    
    try:
        print(f"Attempting to download image for {country_name}")
        response = requests.get(url)
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            print(f"Content-Type: {content_type}")
            
            if 'image/png' in content_type:
                print(f"Successfully downloaded PNG image for {country_name}")
                print(f"Image size: {len(response.content)} bytes")
                
                # Save the image to a file
                with open(f"{country_name}.png", 'wb') as f:
                    f.write(response.content)
                
                # Open the image using matplotlib
                img = plt.imread(f"{country_name}.png")
                plt.imshow(img)
                plt.show()
                
            else:
                print(f"Warning: Content-Type is not 'image/png'. Got: {content_type}")
        else:
            print(f"Failed to download image. Status code: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(f"Type of exception: {type(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        country_name = sys.argv[1]
    else:
        country_name = input("Enter country name: ")
    
    test_country_image_request(country_name)
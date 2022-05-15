import json
import urllib
import os
from instagram_private_api import Client, ClientConnectionError, ClientLoginError
from prettytable import PrettyTable
import sys


class InstagramConnection:
    def __init__(self, user):
        username, password = user.values()
        self.target = ''
        self.target_id = ''
        self.target_username = ''
        try:
            self.api = Client(auto_patch=True, authenticate=True, username=username, password=password)
        except ClientLoginError as error:
            raise error
        except ClientConnectionError as error:
            raise error

    def logout(self):
        self.api.logout()

    def get_user(self, username):
        self.target = self.api.username_info(username)
        self.target_id = self.target['user']['pk']
        self.target_username = username
        return self.target

    def get_profile_pic(self):
        hd_pictures = self.target['user']['hd_profile_pic_versions']
        if len(hd_pictures) > 1:
            return hd_pictures[1]['url']
        return hd_pictures[0]['url']

    def get_media_type(self):
        data = []
        counter = 0
        photo_counter = 0
        video_counter = 0

        result = self.api.user_feed(str(self.target_id))
        data.extend(result.get('items', []))

        next_max_id = result.get('next_max_id')
        while next_max_id:
            results = self.api.user_feed(str(self.target_id), max_id=next_max_id)
            data.extend(results.get('items', []))
            next_max_id = results.get('next_max_id')

        for post in data:
            if "media_type" in post:
                if post["media_type"] == 1:
                    photo_counter = photo_counter + 1
                elif post["media_type"] == 2:
                    video_counter = video_counter + 1
                counter = counter + 1
                sys.stdout.write("\rChecked %i" % counter)
                sys.stdout.flush()

        sys.stdout.write(" posts")
        sys.stdout.flush()

        if counter > 0:
            print("\nWoohoo! We found " + str(photo_counter) + " photos and " + str(video_counter) +
                  " video posted by target\n")
        else:
            print("Sorry! No results")

    def get_followers(self):

        _followers = []
        followers = []

        rank_token = Client.generate_uuid()
        data = self.api.user_followers(
            str(self.target_id), rank_token=rank_token)

        _followers.extend(data.get('users', []))

        next_max_id = data.get('next_max_id')
        while next_max_id:
            sys.stdout.write("\rCatched %i followers" % len(_followers))
            sys.stdout.flush()
            results = self.api.user_followers(
                str(self.target_id), rank_token=rank_token, max_id=next_max_id)
            _followers.extend(results.get('users', []))
            next_max_id = results.get('next_max_id')

        for user in _followers:
            u = {
                'id': user['pk'],
                'username': user['username'],
                'full_name': user['full_name']
            }
            followers.append(u)

        t = PrettyTable(['ID', 'Username', 'Full Name'])
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Full Name"] = "l"

        json_data = {}
        followings_list = []

        for node in followers:
            t.add_row([str(node['id']), node['username'], node['full_name'].encode()])

            follow = {
                'id': node['id'],
                'username': node['username'],
                'full_name': node['full_name']
            }
            followings_list.append(follow)

        output_dir = 'C:/Users/elad2/Documents/Photos'
        file_name = output_dir + "/" + self.target_username + "_followers.txt"
        file = open(file_name, "w")
        file.write(str(t))
        file.close()

        json_data['followers'] = followers
        json_file_name = output_dir + "/" + self.target_username + "_followers.json"
        with open(json_file_name, 'w') as f:
            json.dump(json_data, f)

        print(t)
        print(f'followers: {len(followings_list)}')
        return followings_list

    def get_followings(self):

        _followings = []
        followings = []

        rank_token = Client.generate_uuid()
        data = self.api.user_following(
            str(self.target_id), rank_token=rank_token)

        _followings.extend(data.get('users', []))

        next_max_id = data.get('next_max_id')
        while next_max_id:
            sys.stdout.write("\rCatched %i followings" % len(_followings))
            sys.stdout.flush()
            results = self.api.user_following(
                str(self.target_id), rank_token=rank_token, max_id=next_max_id)
            _followings.extend(results.get('users', []))
            next_max_id = results.get('next_max_id')

        for user in _followings:
            u = {
                'id': user['pk'],
                'username': user['username'],
                'full_name': user['full_name']
            }
            followings.append(u)

        t = PrettyTable(['ID', 'Username', 'Full Name'])
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Full Name"] = "l"

        json_data = {}
        followings_list = []

        for node in followings:
            t.add_row([str(node['id']), node['username'], node['full_name'].encode()])

            follow = {
                'id': node['id'],
                'username': node['username'],
                'full_name': node['full_name']
            }
            followings_list.append(follow)

        output_dir = 'C:/Users/elad2/Documents/Photos'
        file_name = output_dir + "/" + self.target_username + "_followings.txt"
        file = open(file_name, "w")
        file.write(str(t))
        file.close()

        json_data['followings'] = followings_list
        json_file_name = output_dir + "/" + self.target_username + "_followings.json"
        with open(json_file_name, 'w') as f:
            json.dump(json_data, f)

        print(t)
        print(f'followings: {len(followings_list)}')
        return followings_list

    def get_unfollowers(self):
        followers = self.get_followers()
        followings = self.get_followings()
        unfollowers = []
        for follow in followings:
            if follow not in followers:
                unfollowers.append(follow)

        t = PrettyTable(['ID', 'Username', 'Full Name'])
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Full Name"] = "l"

        json_data = {}
        unfollowings_list = []

        for node in unfollowers:
            t.add_row([str(node['id']), node['username'], node['full_name'].encode()])

            unfollow = {
                'id': node['id'],
                'username': node['username'],
                'full_name': node['full_name']
            }
            unfollowings_list.append(unfollow)

        output_dir = 'C:/Users/elad2/Documents/Photos'
        file_name = output_dir + "/" + self.target_username + "_unfollowers.txt"
        file = open(file_name, "w")
        file.write(str(t))
        file.close()

        json_data['unfollowers'] = unfollowings_list
        json_file_name = output_dir + "/" + self.target_username + "_unfollowers.json"
        with open(json_file_name, 'w') as f:
            json.dump(json_data, f)

        print(t)
        print(f'unfollowers: {len(unfollowings_list)}\n')

        return unfollowings_list

    def get_user_photos(self):
        output_dir = 'C:/Users/elad2/Documents/Photos'
        os.mkdir(output_dir + f'/{self.target_username}')
        image_urls = []
        data = []
        counter = 0
        result = self.api.user_feed(str(self.target_id))
        data.extend(result.get('items', []))

        next_max_id = result.get('next_max_id')
        while next_max_id:
            results = self.api.user_feed(str(self.target_id), max_id=next_max_id)
            data.extend(results.get('items', []))
            next_max_id = results.get('next_max_id')

        try:
            for item in data:
                if "image_versions2" in item:
                    counter = counter + 1
                    url = item["image_versions2"]["candidates"][0]["url"]
                    photo_id = item["id"]
                    end = output_dir + f"/{self.target_username}" + \
                          "/" + self.target_username + "_" + photo_id + ".jpg"
                    # image_urls.append(url)
                    urllib.request.urlretrieve(url, end)
                    sys.stdout.write("\rDownloaded %i" % counter)
                    sys.stdout.flush()
                else:
                    carousel = item["carousel_media"]
                    for i in carousel:
                        counter = counter + 1
                        url = i["image_versions2"]["candidates"][0]["url"]
                        photo_id = i["id"]
                        end = output_dir + f"/{self.target_username}" + \
                              "/" + self.target_username + "_" + photo_id + ".jpg"
                        # image_urls.append(url)
                        urllib.request.urlretrieve(url, end)
                        sys.stdout.write("\rDownloaded %i" % counter)
                        sys.stdout.flush()

        except AttributeError:
            pass

        except KeyError:
            pass

        sys.stdout.write(" photos")
        sys.stdout.flush()

        print("\nWoohoo! We downloaded " + str(counter) +
              " photos (saved in " + output_dir + '/' + self.target_username + " folder) \n")
        return counter, output_dir + f"/{self.target_username}"

    def get_user_stories(self):
        story_urls = []
        feed = self.api.user_story_feed(self.target_id)
        if feed["reel"]:
            story_items = feed["reel"]["items"]
            for story in story_items:
                if story["media_type"] == 1:
                    story_urls.append({"url": story["image_versions2"]["candidates"][0]["url"], "type": "image"})
                else:
                    story_urls.append({"url": story["video_versions"][0]["url"], "type": "video"})
        return self.target_username, story_urls


    def unfollow_user(self, user_id):
        self.api.friendships_destroy(user_id)


    def unfollow_all(self, unfollow_list):
        for unfollower in unfollow_list:
            self.unfollow_user(unfollower['id'])
{JSON} Placeholder

## Free fake and reliable API for testing and prototyping.

Powered by
[JSON Server](https://github.com/typicode/json-server)
+
[LowDB](https://github.com/typicode/lowdb).


**Serving ~3 billion requests each month**.

## Sponsors

JSONPlaceholder is supported by the following companies and
[Sponsors](https://github.com/sponsors/typicode) on GitHub, check
them out 💖


[![](https://jsonplaceholder.typicode.com/mockend.svg)](https://mockend.com)

[![](https://github.com/typicode/json-server/assets/5502029/928b7526-0fdf-46ae-80d9-27fa0ef5f430)](https://zuplo.link/json-server-web)

[Your company logo here](https://github.com/sponsors/typicode)

## Try it

Run this code here, in a console or from any site:

```
fetch('https://jsonplaceholder.typicode.com/todos/1')
      .then(response => response.json())
      .then(json => console.log(json))
```

```
{}
```

Congrats! You've made your first call to JSONPlaceholder. 😃 🎉


[![Sponsored: Filestack](https://ethicalads.blob.core.windows.net/media/images/2023/06/ethicalads1.png)](https://server.ethicalads.io/proxy/click/8392/019561c8-9d75-7200-868d-90ab8df97f93/)

www.filestack.com

×

## When to use

JSONPlaceholder is a free online REST API that you can use **whenever you need some fake data**. It can be in a README on GitHub, for a demo on CodeSandbox, in code examples on Stack Overflow, ...or simply to test things locally.

## Resources

JSONPlaceholder comes with a set of 6 common resources:

[/posts](https://jsonplaceholder.typicode.com/posts)100 posts[/comments](https://jsonplaceholder.typicode.com/comments)500 comments[/albums](https://jsonplaceholder.typicode.com/albums)100 albums[/photos](https://jsonplaceholder.typicode.com/photos)5000 photos[/todos](https://jsonplaceholder.typicode.com/todos)200 todos[/users](https://jsonplaceholder.typicode.com/users)10 users

**Note**: resources have relations. For example: posts have many comments, albums have many photos, ... see [guide](https://jsonplaceholder.typicode.com/guide) for the full list.

## Routes

All HTTP methods are supported. You can use http or https for your requests.

GET[/posts](https://jsonplaceholder.typicode.com/posts)GET[/posts/1](https://jsonplaceholder.typicode.com/posts/1)GET[/posts/1/comments](https://jsonplaceholder.typicode.com/posts/1/comments)GET[/comments?postId=1](https://jsonplaceholder.typicode.com/comments?postId=1)POST/postsPUT/posts/1PATCH/posts/1DELETE/posts/1

**Note**: see [guide](https://jsonplaceholder.typicode.com/guide) for usage examples.

## Use your own data

With our sponsor [Mockend](https://mockend.com) and a simple GitHub repo, you can have your own fake online REST server in seconds.
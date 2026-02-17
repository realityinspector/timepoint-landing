FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY docs/images/ /usr/share/nginx/html/docs/images/
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]

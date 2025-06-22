FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf

# Copy frontend static and template files
COPY frontend/static /usr/share/nginx/html/static
COPY frontend/templates /usr/share/nginx/html/templates

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
docker build -t recommender .

docker run --name reco -d --rm -p8080:8080 recommender
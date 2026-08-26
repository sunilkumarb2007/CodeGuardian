FROM maven:3.9.11-eclipse-temurin-21 AS build
WORKDIR /app

COPY pom.xml pom.xml
COPY gateway/pom.xml gateway/pom.xml
COPY order-service/pom.xml order-service/pom.xml
COPY payment-service/pom.xml payment-service/pom.xml

RUN mvn -q -pl order-service -am dependency:go-offline

COPY . .
RUN mvn -q -pl order-service -am package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /service
COPY --from=build /app/order-service/target/order-service-0.0.1-SNAPSHOT.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java","-jar","app.jar"]

#!groovy

def tryStep(String message, Closure block, Closure tearDown = null) {
    try {
        block();
    }
    catch (Throwable t) {
        slackSend message: "${env.JOB_NAME}: ${message} failure ${env.BUILD_URL}", channel: '#ci-channel', color: 'danger'

        throw t;
    }
    finally {
        if (tearDown) {
            tearDown();
        }
    }
}


node {

    stage("Checkout") {
        checkout scm
    }

    stage('Test') {
        tryStep "test", {
            sh "docker-compose -p basiskaart -f src/.jenkins/test/docker-compose.yml build"
        }, {
            sh "docker-compose -p basiskaart -f src/.jenkins/test/docker-compose.yml down"
        }
    }

    stage("Build acceptance image") {
        tryStep "build", {
            def image = docker.build("build.datapunt.amsterdam.nl:5000/datapunt/basiskaart:${env.BUILD_NUMBER}", "data_import")
            image.push()
            image.push("acceptance")
        }
    }
}

stage('Waiting for approval') {
    slackSend channel: '#ci-channel', color: 'warning', message: 'Basiskaart is waiting for Production Release - please confirm'
    input "Deploy to Production?"
}

node {
    stage('Push production image') {
    tryStep "image tagging", {
        def image = docker.image("build.datapunt.amsterdam.nl:5000/datapunt/basiskaart:${env.BUILD_NUMBER}")
        image.pull()

            image.push("production")
            image.push("latest")
        }
    }
}

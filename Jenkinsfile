pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    component: jenkins-agent
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    supplementalGroups: [984]
  containers:
  - name: docker-cli
    image: docker:24.0.7-cli
    imagePullPolicy: IfNotPresent
    command: ['cat']
    tty: true
    volumeMounts:
    - mountPath: /var/run/docker.sock
      name: docker-sock
  - name: jnlp
    image: host.k3d.internal:5000/jenkins/inbound-agent:latest
    imagePullPolicy: IfNotPresent
    volumeMounts:
    - mountPath: /var/run/docker.sock
      name: docker-sock
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
"""
        }
    }

    environment {
        NEXUS_URL = 'host.k3d.internal:5000'
        IMAGE_NAME = 'myapp-flask'
        // Задаём каталог для Docker-конфига, доступный для пользователя 1000
        DOCKER_CONFIG = '/home/jenkins/.docker'
    }

    stages {
        stage('Checkout') {
            steps {
                script { 
                    checkout scm
                    env.COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    // Выводим для отладки
                    echo "COMMIT = ${env.COMMIT}"
                    echo "IMAGE_NAME = ${env.IMAGE_NAME}"
                }
            }
        }

        stage('Prepare Docker Config') {
            steps {
                container('docker-cli') {
                    script {
                        // Создаём каталог для конфига и устанавливаем права (на случай, если он не существует)
                        sh """
                            mkdir -p ${DOCKER_CONFIG}
                            chmod 700 ${DOCKER_CONFIG}
                        """
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('docker-cli') {
                    script {
                        // Проверяем, что переменные не пустые
                        if (!env.COMMIT || !env.IMAGE_NAME) {
                            error "Переменные IMAGE_NAME или COMMIT пустые!"
                        }
                        sh "docker build -t ${IMAGE_NAME}:${COMMIT} ."
                    }
                }
            }
        }

        stage('Push to Nexus') {
            steps {
                container('docker-cli') {
                    script {
                        sh "docker tag ${IMAGE_NAME}:${COMMIT} ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}"
                        withCredentials([usernamePassword(
                            credentialsId: 'nexus-creds',
                            usernameVariable: 'NEXUS_USER',
                            passwordVariable: 'NEXUS_PASS'
                        )]) {
                            sh """
                                docker login -u ${NEXUS_USER} -p ${NEXUS_PASS} ${NEXUS_URL}
                                docker push ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}
                            """
                        }
                    }
                }
            }
        }

        stage('Update GitOps') {
            steps {   
                script {
                    sshagent(['git-key']) {
                        sh """
                            rm -rf gitops-tmp
                            git -c core.sshCommand="ssh -o StrictHostKeyChecking=no" clone git@github.com:endlessf1re/gitops.git gitops-tmp
                            cd gitops-tmp
                            sed -i "s|image: .*|image: ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}|g" apps/myapp/deployment.yaml
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@local"
                            git add .
                            git commit -m "Update image to ${COMMIT} [skip ci]"
                            git push origin main
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            sh "rm -rf gitops-tmp"
        }
    }
}

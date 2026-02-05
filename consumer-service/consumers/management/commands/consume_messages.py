"""
Django management command to run the Kafka consumer.
Usage: python manage.py consume_messages
"""
import logging
from django.core.management.base import BaseCommand
from consumers.kafka_consumer import KafkaMessageConsumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start Kafka consumer to process customer and inventory messages'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--log-level',
            type=str,
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Set logging level'
        )
    
    def handle(self, *args, **options):
        log_level = options['log_level']
        logging.getLogger('consumers').setLevel(getattr(logging, log_level))
        
        self.stdout.write(self.style.SUCCESS('Starting Kafka consumer...'))
        self.stdout.write(f'Log level: {log_level}')
        
        try:
            consumer = KafkaMessageConsumer()
            consumer.start()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Consumer failed: {e}'))
            logger.error(f'Consumer failed: {e}', exc_info=True)
            raise
